"""Simple Flask dashboard to view portfolio.json

Run: `python3 src/web_dashboard.py` (port configurable via PORT env var, default 8000)
"""
from __future__ import annotations

import json
import os
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
try:
    from flask_cors import CORS
except Exception:
    CORS = None

# Try to import the financial helper to fetch live prices; fall back gracefully
try:
    from finance_server import get_financial_data
except Exception:
    get_financial_data = None

load_dotenv()

PORTFOLIO_FILE = os.getenv("PORTFOLIO_FILE", "portfolio.json")
PORT = int(os.getenv("PORT", "8000"))

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
if CORS:
    # allow cross-origin requests from the frontend (Vercel or local ngrok)
    CORS(app)


def _read_portfolio() -> Dict:
    if not os.path.exists(PORTFOLIO_FILE):
        return {"cash": 0.0, "positions": {}, "transactions": []}
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/api/portfolio")
def api_portfolio():
    """Return raw portfolio JSON."""
    return jsonify(_read_portfolio())


@app.route("/")
def dashboard():
    """Render a simple dashboard with cash, positions and transactions."""
    data = _read_portfolio()
    cash = data.get("cash", 0.0)
    positions = data.get("positions", {})
    transactions = list(reversed(data.get("transactions", [])))[:50]

    # compute position values if 'last_price' present in position, otherwise show avg
    rows = []
    total_value = float(cash)
    for sym, info in positions.items():
        q = int(info.get("quantity", 0))
        avg = float(info.get("avg_price", 0.0))
        # attempt to fetch live price if helper is available
        price = avg
        if get_financial_data:
            try:
                fd = get_financial_data(sym)
                p = fd.get("price")
                if p:
                    price = float(p)
            except Exception:
                # keep avg as fallback
                price = avg

        value = price * q
        total_value += value
        rows.append({"symbol": sym, "quantity": q, "avg": avg, "price": price, "value": value})

    return render_template(
        "dashboard.html",
        cash=cash,
        positions=rows,
        transactions=transactions,
        total_value=total_value,
    )


def run():
    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    run()
