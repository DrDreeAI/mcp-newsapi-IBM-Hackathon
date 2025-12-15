"""Finance MCP server

This module exposes MCP tools to support three Watsonx agents:
- Expert Tech (uses `search_news(topic='technology')`)
- Financial Analyst (uses `search_news(topic='finance')` and `get_financial_data`)
- Portfolio Manager (uses `execute_investment` and `get_portfolio_report`)

Tools are exposed as `@mcp.tool()` functions using `FastMCP`.
Configuration is via environment variables loaded from a local `.env` file.
Persistence: `portfolio.json` holds cash, positions and transaction history.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - graceful fallback for local tests
    FastMCP = None

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
NEWSAPI_COUNTRY = os.getenv("NEWSAPI_COUNTRY", "us")

PORTFOLIO_FILE = os.getenv("PORTFOLIO_FILE", "portfolio.json")
INITIAL_CASH = float(os.getenv("INITIAL_CASH", "10000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finance_server")


def _ensure_portfolio_file() -> None:
    """Ensure `portfolio.json` exists with initial structure."""
    if not os.path.exists(PORTFOLIO_FILE):
        data = {"cash": INITIAL_CASH, "positions": {}, "transactions": []}
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def _read_portfolio() -> Dict:
    _ensure_portfolio_file()
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_portfolio(data: Dict) -> None:
    tmp = PORTFOLIO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, PORTFOLIO_FILE)


if FastMCP:
    mcp = FastMCP()
else:
    # Provide a noop decorator for local development/testing
    class _Dummy:
        def tool(self):
            def deco(fn):
                return fn

            return deco


    mcp = _Dummy()


@mcp.tool()
def search_news(query: str, topic: str = "") -> List[Dict[str, str]]:
    """Search news and return up to 5 articles.

    Args:
        query: search query keywords.
        topic: 'technology' or 'finance' (controls filtering).

    Returns:
        A list of articles (dict) with keys: 'source', 'title', 'summary', 'url'.
    """
    if not NEWSAPI_KEY:
        raise RuntimeError("NEWSAPI_KEY is not configured")

    headers = {"User-Agent": "mcp-newsapi/1.0", "Accept": "application/json"}

    # Choose endpoint and params by topic
    if topic.lower() == "technology":
        url = "https://newsapi.org/v2/top-headlines"
        params = {"category": "technology", "pageSize": 5, "q": query, "apiKey": NEWSAPI_KEY}
    else:
        # For finance or general queries, use everything endpoint and search the query or 'finance'
        url = "https://newsapi.org/v2/everything"
        q = f"{query} finance" if topic.lower() == "finance" else query
        params = {"q": q or "finance", "pageSize": 5, "sortBy": "publishedAt", "apiKey": NEWSAPI_KEY}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        payload = r.json()
        articles = payload.get("articles", [])[:5]
        out = []
        for a in articles:
            out.append({
                "source": a.get("source", {}).get("name"),
                "title": a.get("title"),
                "summary": a.get("description") or a.get("content") or "",
                "url": a.get("url"),
            })
        return out
    except requests.RequestException as e:
        logger.error("NewsAPI request failed: %s", e)
        raise RuntimeError(f"NewsAPI request failed: {e}")


@mcp.tool()
def get_financial_data(symbol: str) -> Dict[str, Optional[str]]:
    """Get financial data for a symbol (price, marketCap, PER if available).

    Tries Alpha Vantage first, then falls back to Yahoo via RapidAPI.
    """
    symbol = symbol.upper().strip()

    result = {"symbol": symbol, "price": None, "marketCap": None, "PER": None}

    if ALPHA_VANTAGE_KEY:
        try:
            # GLOBAL_QUOTE for current price
            gq = requests.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": ALPHA_VANTAGE_KEY},
                timeout=10,
            )
            gq.raise_for_status()
            gdata = gq.json()
            quote = gdata.get("Global Quote", {})
            price = quote.get("05. price")
            if price:
                result["price"] = price

            # Try OVERVIEW to get MarketCapitalization and PERatio
            ov = requests.get(
                "https://www.alphavantage.co/query",
                params={"function": "OVERVIEW", "symbol": symbol, "apikey": ALPHA_VANTAGE_KEY},
                timeout=10,
            )
            ov.raise_for_status()
            odata = ov.json()
            if odata:
                mc = odata.get("MarketCapitalization")
                pe = odata.get("PERatio") or odata.get("PE")
                if mc:
                    result["marketCap"] = mc
                if pe:
                    result["PER"] = pe

            if result["price"]:
                return result
        except requests.RequestException as e:
            logger.info("AlphaVantage call failed, falling back to RapidAPI: %s", e)

    # Fallback to Yahoo via RapidAPI
    if RAPIDAPI_KEY:
        try:
            url = f"https://yahoo-finance15.p.rapidapi.com/api/yahoo/qu/quote/{symbol}"
            headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "yahoo-finance15.p.rapidapi.com"}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            j = r.json()
            # attempt to extract price and market cap
            price = None
            mc = None
            if isinstance(j, dict):
                # nested structures differ; attempt common keys
                quote = j.get("quote") or j.get("price") or {}
                price = quote.get("regularMarketPrice") or quote.get("regularMarketPreviousClose")
                if isinstance(price, dict):
                    price = price.get("raw")
                mc = quote.get("marketCap")
                if isinstance(mc, dict):
                    mc = mc.get("raw")
            if price:
                result["price"] = str(price)
            if mc:
                result["marketCap"] = str(mc)
            return result
        except requests.RequestException as e:
            logger.error("RapidAPI Yahoo call failed: %s", e)

    raise RuntimeError("Could not retrieve financial data for symbol: %s" % symbol)


@mcp.tool()
def execute_investment(symbol: str, quantity: int, price: float, rationale: str = "") -> Dict[str, str]:
    """Execute an investment purchase.

    Args:
        symbol: stock symbol
        quantity: number of shares (int)
        price: price per share to execute
        rationale: textual reason for the trade

    Returns:
        A dict with 'status' and 'message'.
    """
    if quantity <= 0 or price <= 0:
        return {"status": "error", "message": "Quantity and price must be positive values."}

    portfolio = _read_portfolio()
    total_cost = float(quantity) * float(price)
    cash = float(portfolio.get("cash", 0))
    if total_cost > cash:
        return {"status": "error", "message": f"Insufficient cash: need ${total_cost:.2f}, available ${cash:.2f}"}

    # Deduct cash and add position
    portfolio["cash"] = round(cash - total_cost, 2)
    positions = portfolio.setdefault("positions", {})
    pos = positions.get(symbol, {"quantity": 0, "avg_price": 0.0})
    prev_q = pos.get("quantity", 0)
    prev_avg = float(pos.get("avg_price", 0))
    new_q = prev_q + quantity
    new_avg = ((prev_avg * prev_q) + (price * quantity)) / new_q if new_q else 0.0
    positions[symbol] = {"quantity": new_q, "avg_price": round(new_avg, 4)}

    # Log transaction
    tx = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "total": round(total_cost, 2),
        "rationale": rationale,
    }
    portfolio.setdefault("transactions", []).append(tx)
    _write_portfolio(portfolio)

    return {"status": "success", "message": f"Bought {quantity} {symbol} for ${total_cost:.2f}. New cash: ${portfolio['cash']:.2f}"}


@mcp.tool()
def get_portfolio_report() -> str:
    """Return a human-readable summary of the portfolio.

    Includes cash and positions. Also computes an approximate market value per position using `get_financial_data` when available.
    """
    portfolio = _read_portfolio()
    cash = float(portfolio.get("cash", 0.0))
    positions = portfolio.get("positions", {})
    lines = [f"Cash: ${cash:,.2f}", "Positions:"]
    total_value = cash
    for sym, info in positions.items():
        q = int(info.get("quantity", 0))
        avg = float(info.get("avg_price", 0.0))
        # Try to get current price; ignore errors
        try:
            fd = get_financial_data(sym)
            price = float(fd.get("price") or avg)
        except Exception:
            price = avg
        value = price * q
        total_value += value
        lines.append(f"- {sym}: qty={q}, avg=${avg:.2f}, current=${price:.2f}, value=${value:,.2f}")
    lines.append(f"Total portfolio approx: ${total_value:,.2f}")
    return "\n".join(lines)


def _register_basic_info() -> None:
    """Log startup info and basic validation of env variables."""
    logger.info("Starting Python Finance MCP server")
    if not NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set; search_news will fail until configured.")
    if not ALPHA_VANTAGE_KEY:
        logger.info("ALPHA_VANTAGE_KEY not set; get_financial_data will try RapidAPI fallback only.")
    _ensure_portfolio_file()


if __name__ == "__main__":
    _register_basic_info()
    # Try to run the MCP server if FastMCP implements a run/connect method
    if FastMCP and hasattr(mcp, "run"):
        # Some versions expose .run() for CLI; call it if present
        try:
            mcp.run()
        except Exception as e:
            logger.error("Failed to run FastMCP: %s", e)
            logger.info("You can run this module under an MCP runner that uses stdio transport.")
    else:
        # Provide a small smoke test CLI
        logger.info("FastMCP CLI not available in this environment. Running a smoke test of tools.")
        print("Smoke test - available tools: search_news, get_financial_data, execute_investment, get_portfolio_report")
