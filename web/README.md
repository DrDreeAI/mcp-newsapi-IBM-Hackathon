# Plagists Wallet (web)

This folder is a self-contained React frontend for the Plagists Wallet. It can be used as a standalone repository and deployed to Vercel (or other static hosts).

Key points
- The frontend expects an API endpoint `/api/portfolio` on a backend host that returns the portfolio JSON used by the app.
- Configure the backend URL using the `VITE_API_URL` environment variable. If unset, the app will try the relative path `/api/portfolio`.

Local development

1. Install deps

```bash
npm install
```

2. Run dev server

```bash
npm run dev
```

3. To test against a local backend (MCP or Flask dashboard) running on `http://localhost:8000`, create a `.env.local` file containing:

```
VITE_API_URL=http://localhost:8000
```

Production build

```bash
npm run build
# preview locally
npm start
```

Deploy to Vercel (drag & drop)

1. Zip or drag the `web` folder into Vercel's dashboard to create a new project.
2. In Vercel project settings -> Environment Variables, set `VITE_API_URL` to the public URL of your backend (for example your deployed MCP server or the public ngrok URL).
3. Deploy — Vercel will run `npm run build` and serve the generated build.

Notes about backend
- If your backend exposes `http://your-backend/api/portfolio`, the frontend will work. For `https`/different domains, make sure the backend allows CORS for the deployed frontend origin.
- For a production-ready setup, consider moving from `portfolio.json` to a database (Supabase, Postgres, etc.) and exposing a proper REST API.

Connecting to your local MCP quickly (ngrok)

1. Start your MCP backend (SSE) locally on port 8000, e.g.:

```bash
mcp run src/finance_server.py --transport sse --port 8000
# or run the Flask dashboard `src/web_dashboard.py` which exposes `/api/portfolio` on the same host
```

2. In a new terminal start ngrok and copy the HTTPS forwarding URL:

```bash
ngrok http 8000
```

3. Set `VITE_API_URL` in Vercel (or in your local `.env.local`) to the ngrok HTTPS URL (no trailing slash). Example:

```
VITE_API_URL=https://a1b2-c3d4.ngrok-free.app
```

4. Make sure the backend allows CORS for the frontend origin (for `src/web_dashboard.py` add Flask-CORS or adjust headers). For example, install `flask-cors` and add `CORS(app)` to the Flask app.

