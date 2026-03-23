#!/usr/bin/env python3
"""
VERA startup script.

Usage:
    python run.py               # start server (reads .env)
    python run.py --no-browser  # start without opening browser
"""

import os
import sys
import time
import webbrowser
import threading

import uvicorn
from dotenv import load_dotenv

load_dotenv()


def open_browser(url: str, delay: float = 1.5) -> None:
    """Open the browser after a short delay to let the server start."""
    time.sleep(delay)
    webbrowser.open(url)


def main() -> None:
    host = os.getenv("VERA_HOST", "127.0.0.1")
    port = int(os.getenv("VERA_PORT", "8000"))
    open_browser_flag = "--no-browser" not in sys.argv

    url = f"http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}"

    print("=" * 60)
    print("  VERA — Verification, Execution, Reasoning, Arbitration")
    print("=" * 60)
    print(f"  Server  : {url}")
    print(f"  API Docs: {url}/docs")
    print(f"  Model   : {os.getenv('VERA_MODEL', 'gpt-4o-mini')}")
    base_url = os.getenv("VERA_BASE_URL", "")
    if base_url:
        print(f"  Base URL: {base_url}")
    print("=" * 60)
    print("  Press Ctrl+C to stop.")
    print()

    if open_browser_flag:
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    uvicorn.run(
        "vera.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
