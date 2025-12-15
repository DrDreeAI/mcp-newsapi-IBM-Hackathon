#!/usr/bin/env python3
"""
SSE Server Launcher for Finance MCP Server

This script launches the FastMCP finance server in SSE (Server-Sent Events) mode,
making it accessible via HTTP/HTTPS for external services like watsonx.

Usage:
    python start_sse_server.py [--port PORT] [--host HOST]

Default: http://0.0.0.0:8000
"""

import argparse
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import the FastMCP instance from finance_server
from finance_server import mcp, _register_basic_info


def main():
    parser = argparse.ArgumentParser(
        description="Launch Finance MCP Server in SSE mode"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0 for all interfaces)"
    )
    args = parser.parse_args()

    # Set environment variable to disable host validation
    import os
    os.environ["MCP_ALLOW_HTTP"] = "1"
    os.environ["MCP_DISABLE_HOST_VALIDATION"] = "1"

    # Initialize portfolio and log startup info
    _register_basic_info()

    print(f"\n{'='*60}")
    print(f"🚀 Starting Finance MCP Server in SSE mode")
    print(f"{'='*60}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"URL:  http://{args.host}:{args.port}")
    print(f"{'='*60}\n")
    print("Available tools:")
    print("  - search_news(query, topic)")
    print("  - get_financial_data(symbol)")
    print("  - execute_investment(symbol, quantity, price, rationale)")
    print("  - get_portfolio_report()")
    print(f"\n{'='*60}")
    print("💡 To expose this server via ngrok, run in another terminal:")
    print(f"   ngrok http {args.port}")
    print(f"{'='*60}\n")

    # Run the server in SSE mode
    try:
        import uvicorn
        # FastMCP provides an ASGI app via the .sse_app property
        app = mcp.sse_app()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped gracefully")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
