# MCP News API Server

A Model Context Protocol (MCP) server that exposes endpoints from the News API (https://newsapi.org) to search for and retrieve news articles. This server allows programmatic access to news data via the MCP protocol.

## Prerequisites

- Node.js (v18 or later recommended)
- npm (comes with Node.js)
- A News API key (get one from https://newsapi.org)
- (Optional) MCP-compatible client or runner (e.g., VSCode extension, CLI)

## Setup

1. **Clone the repository or ensure you are in the project directory.**

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Build the server:**
   ```bash
   npm run build
   ```
   This will create a `build` directory with the compiled JavaScript code.

4. **Set your News API Key:**
   The server reads the API key from the `NEWSAPI_KEY` environment variable. Set this variable in your environment before running the server.
   Example (Bash/Zsh):
   ```bash
   export NEWSAPI_KEY="YOUR_API_KEY"
   ```
   Replace `"YOUR_API_KEY"` with your actual News API key.

## Running the Server

- **Directly:**
  Ensure the `NEWSAPI_KEY` environment variable is set, then run:
  ```bash
  node build/index.js
  ```
  or, if you have a start script:
  ```bash
  npm run start
  ```

- **Via MCP runner:**
  Configure your MCP client to run the server using stdio transport. You will also need to configure the environment variable for the API key within your MCP runner's settings.
  Example MCP settings entry:
  ```json
  "mcp-newsapi": {
    "transportType": "stdio",
    "command": "node",
    "args": [
      "/path/to/mcp-newsapi/build/index.js"
    ],
    "environment": {
      "NEWSAPI_KEY": "YOUR_API_KEY"
    }
    // ... other optional settings ...
  }
  ```
  Replace `"YOUR_API_KEY"` with your actual News API key.

## Available Tools

The server exposes the following tools via MCP, corresponding to News API endpoints:

### **search_articles**
- **Description:** Searches for news articles using the News API "Everything" endpoint.
- **Input:**
  - `q` (string, required): Keywords or phrases to search for in the article title and body.
  - `sources` (string, optional): A comma-separated string of identifiers for the news sources or blogs you want headlines from.
  - `domains` (string, optional): A comma-separated string of domains (e.g. bbc.co.uk, techcrunch.com) to search within.
  - `excludeDomains` (string, optional): A comma-separated string of domains (e.g. bbc.co.uk, techcrunch.com) to exclude from the search.
  - `from` (string, optional): A date and optional time for the oldest article allowed. Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (e.g. 2024-01-01 or 2024-01-01T10:00:00).
  - `to` (string, optional): A date and optional time for the newest article allowed. Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.
  - `language` (string, optional): The 2-letter ISO 639-1 code of the language you want to get headlines for. Possible options: ar, de, en, es, fr, he, it, nl, no, pt, ru, sv, ud, zh. Default: all languages returned.
  - `sortBy` (enum: 'relevancy', 'popularity', 'publishedAt', optional): The order to sort the articles in. Possible options: relevancy, popularity, publishedAt. Default: relevancy.
  - `pageSize` (integer, optional, default 100): The number of results to return per page (request). 20 is the default, 100 is the maximum.
  - `page` (integer, optional, default 1): Use this to page through the results if the total results found is greater than the pageSize.
- **Output:**
  - An object containing `status`, `totalResults`, and an array of `articles` with details like source, author, title, description, URL, image URL, published date, and content.

### **get_top_headlines**
- **Description:** Fetches top news headlines using the News API "Top Headlines" endpoint.
- **Input:**
  - `q` (string, optional): Keywords or phrases to search for in the article title and body.
  - `sources` (string, optional): A comma-separated string of identifiers for the news sources or blogs you want headlines from.
  - `category` (enum: 'business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology', optional): The category you want to get headlines for. Possible options: business, entertainment, general, health, science, sports, technology.
  - `language` (string, optional): The 2-letter ISO 639-1 code of the language you want to get headlines for. Possible options: ar, de, en, es, fr, he, it, nl, no, pt, ru, sv, ud, zh. Default: all languages returned.
  - `country` (string, optional): The 2-letter ISO 3166-1 country code of the country you want to get headlines for. Possible options: ae, ar, at, au, be, bg, br, ca, ch, cn, co, cu, cz, de, eg, fr, gb, gr, hk, hu, id, ie, il, in, it, jp, kr, lt, lv, ma, mx, my, ng, nl, no, nz, ph, pl, pt, ro, rs, ru, sa, se, sg, si, sk, th, tr, tw, ua, us, ve, za. Default: all countries returned.
  - `pageSize` (integer, optional, default 100): The number of results to return per page (request). 20 is the default, 100 is the maximum.
  - `page` (integer, optional, default 1): Use this to page through the results if the total results found is greater than the pageSize.
- **Output:**
  - An object containing `status`, `totalResults`, and an array of `articles` with details like source, author, title, description, URL, image URL, published date, and content.

## Error Handling

The server attempts to provide meaningful error messages based on the News API response. If an API call fails, the tool will throw an error with details about the failure, including the News API error message and code if available.

## Extending

To add more News API endpoints as tools, create a new TypeScript file in `src/tools/`, define its input schema using Zod, implement the handler function to call the News API SDK, and export the tool definition. Then, import and register the new tool in `src/tools/index.ts`.

## Python helpers (optional)

This repository also includes a small Python module (`src/finance_server.py`) that provides MCP tools for finance-related APIs (Yahoo via RapidAPI, NewsAPI, Alpha Vantage). It reads API keys from a local `.env` file using `python-dotenv`.

- **Create a `.env` file** in the project root (do not commit it). Example keys are listed in `.env.example`.
- **Install dependencies** (example):

```bash
python -m pip install --upgrade pip
python -m pip install python-dotenv requests
```

- **Quick test** (run locally after adding real keys to `.env`):

```bash
python src/finance_server.py
```

The `get_yahoo_data_via_snippet` tool inside `src/finance_server.py` implements the RapidAPI snippet adapted to MCP and uses `RAPIDAPI_KEY` from the environment.

### Yahoo options via RapidAPI

You can call the Yahoo options endpoint (RapidAPI hosted at `yahoo-finance-real-time1.p.rapidapi.com`) using the helper `get_yahoo_options_via_snippet(symbol, lang='en-US', region='US')` in `src/finance_server.py`.

Curl example:

```bash
curl --request GET \
  --url 'https://yahoo-finance-real-time1.p.rapidapi.com/stock/get-options?symbol=WOOF&lang=en-US&region=US' \
  --header 'x-rapidapi-host: yahoo-finance-real-time1.p.rapidapi.com' \
  --header "x-rapidapi-key: $RAPIDAPI_KEY"
```

In Python (MCP tool):

```python
from finance_server import get_yahoo_options_via_snippet
print(get_yahoo_options_via_snippet('WOOF'))
```

Note: you must set `RAPIDAPI_KEY` in your `.env` for the call to succeed; otherwise RapidAPI replies with an "Invalid API key" message.

## Portfolio Dashboard (web)

A simple Flask dashboard is available at `src/web_dashboard.py` and displays the contents of `portfolio.json`.

1. Install or update Python deps:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

2. Run the dashboard locally (default port 8000):

```bash
python3 src/web_dashboard.py
# then open http://localhost:8000/
```

The dashboard auto-refreshes every 30s and exposes the raw JSON at `/api/portfolio`.
