"""finance_server.py

MCP tools for finance-related APIs.

Load API keys from a local .env file (use python-dotenv).
"""
from __future__ import annotations

import os
import http.client
import json
import logging
from dotenv import load_dotenv

try:
    from mcp.server.fastmcp import FastMCP
    MCPF_AVAILABLE = True
except Exception:
    # Fallback so the module can be executed for local testing without the MCP package.
    MCPF_AVAILABLE = False

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
NEWSAPI_COUNTRY = os.getenv("NEWSAPI_COUNTRY", "us")

if MCPF_AVAILABLE:
    mcp = FastMCP()
else:
    logging.warning(
        "Could not import 'mcp'. Continuing with a noop decorator so tools can be tested locally."
    )

    class _DummyMCP:
        def tool(self):
            def decorator(fn):
                return fn

            return decorator

    mcp = _DummyMCP()

if not (NEWSAPI_KEY and ALPHA_VANTAGE_KEY and RAPIDAPI_KEY):
    logging.warning("One or more API keys are not set. Check your .env file.")


@mcp.tool()
def get_yahoo_data_via_snippet(symbol: str) -> str:
    """Récupère les infos Yahoo via le code snippet RapidAPI adapté."""

    if RAPIDAPI_KEY is None:
        return "Erreur: RAPIDAPI_KEY non configurée"

    conn = http.client.HTTPSConnection("yahoo-finance15.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,  # Utilisez la variable, pas la clé en dur
        "x-rapidapi-host": "yahoo-finance15.p.rapidapi.com",
    }

    endpoint = f"/api/yahoo/qu/quote/{symbol}"

    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
    except Exception as e:
        return f"Erreur lors de l'appel API : {str(e)}"


@mcp.tool()
def get_yahoo_options_via_snippet(symbol: str, lang: str = "en-US", region: str = "US") -> str:
    """Récupère les options d'un symbole via l'endpoint RapidAPI "yahoo-finance-real-time1".

    Exemple RapidAPI curl (adapté) :

    curl --request GET \
      --url 'https://yahoo-finance-real-time1.p.rapidapi.com/stock/get-options?symbol=WOOF&lang=en-US&region=US' \
      --header 'x-rapidapi-host: yahoo-finance-real-time1.p.rapidapi.com' \
      --header 'x-rapidapi-key: VOTRE_CLE_ICI'

    Utilise la variable d'environnement `RAPIDAPI_KEY` (chargée via `.env`).
    """

    if RAPIDAPI_KEY is None:
        return "Erreur: RAPIDAPI_KEY non configurée"

    host = "yahoo-finance-real-time1.p.rapidapi.com"
    conn = http.client.HTTPSConnection(host)

    endpoint = f"/stock/get-options?symbol={symbol}&lang={lang}&region={region}"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": host,
        "Accept": "application/json",
    }

    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()

        # ensure valid JSON when possible
        txt = data.decode("utf-8")
        try:
            json.loads(txt)
            return txt
        except Exception:
            return txt
    except Exception as e:
        return f"Erreur lors de l'appel RapidAPI (options) : {str(e)}"


@mcp.tool()
def get_top_headlines_newsapi(country: str = NEWSAPI_COUNTRY) -> str:
    """Récupère les top headlines via NewsAPI (raw JSON string)."""

    if NEWSAPI_KEY is None:
        return "Erreur: NEWSAPI_KEY non configurée"

    conn = http.client.HTTPSConnection("newsapi.org")
    endpoint = f"/v2/top-headlines?country={country}&apiKey={NEWSAPI_KEY}"

    headers = {
        "User-Agent": "mcp-newsapi/1.0",
        "Accept": "application/json",
    }

    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
    except Exception as e:
        return f"Erreur lors de l'appel NewsAPI : {str(e)}"


@mcp.tool()
def get_alpha_vantage_quote(symbol: str) -> str:
    """Récupère une quote via Alpha Vantage (GLOBAL_QUOTE)."""

    if ALPHA_VANTAGE_KEY is None:
        return "Erreur: ALPHA_VANTAGE_KEY non configurée"

    conn = http.client.HTTPSConnection("www.alphavantage.co")
    endpoint = f"/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"

    try:
        conn.request("GET", endpoint)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
    except Exception as e:
        return f"Erreur lors de l'appel AlphaVantage : {str(e)}"


if __name__ == "__main__":
    # Smoke tests (local only — ensure .env is present with real keys)
    print("Yahoo AAPL:", get_yahoo_data_via_snippet("AAPL"))
    print("NewsAPI top headlines:", get_top_headlines_newsapi())
    print("AlphaVantage IBM:", get_alpha_vantage_quote("IBM"))
