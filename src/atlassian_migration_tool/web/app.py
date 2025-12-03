"""
FastAPI Web Application for Atlassian Migration Tool

This module provides the main FastAPI application with WSL-compatible
browser launching and web-based GUI.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from threading import Timer

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

# Get the directory containing this file
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Create FastAPI app
app = FastAPI(
    title="Jira Migration Tool",
    description="Web-based GUI for migrating Jira content to open-source alternatives",
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux."""
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def open_browser(url: str) -> None:
    """
    Open browser - works in WSL, native Linux, Windows, and macOS.

    In WSL, this uses cmd.exe to launch the Windows default browser,
    avoiding the xdg-open issues that can cause Remote Desktop to launch.
    """
    try:
        if is_wsl():
            # WSL: use Windows browser via cmd.exe
            # This avoids xdg-open which can trigger Remote Desktop
            subprocess.run(
                ["cmd.exe", "/c", f"start {url}"],
                check=False,
                capture_output=True,
            )
            logger.info(f"Opened browser (WSL): {url}")
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", url], check=False, capture_output=True)
            logger.info(f"Opened browser (Linux): {url}")
        elif platform.system() == "Darwin":
            subprocess.run(["open", url], check=False, capture_output=True)
            logger.info(f"Opened browser (macOS): {url}")
        elif platform.system() == "Windows":
            os.startfile(url)  # type: ignore
            logger.info(f"Opened browser (Windows): {url}")
        else:
            logger.warning(f"Unknown platform, cannot open browser: {platform.system()}")
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")


# Import and include routers (must be after app creation to avoid circular imports)
from atlassian_migration_tool.web.routes import (  # noqa: E402
    config,
    connections,
    extract,
    status,
    transform,
    upload,
)

app.include_router(config.router, prefix="/api/config", tags=["Configuration"])
app.include_router(connections.router, prefix="/api/connections", tags=["Connections"])
app.include_router(extract.router, prefix="/api/extract", tags=["Extract"])
app.include_router(transform.router, prefix="/api/transform", tags=["Transform"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Render the configuration page."""
    return templates.TemplateResponse("config.html", {"request": request})


@app.get("/operations", response_class=HTMLResponse)
async def operations_page(request: Request):
    """Render the operations page (extract/transform/upload)."""
    return templates.TemplateResponse("operations.html", {"request": request})


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Render the logs page."""
    return templates.TemplateResponse("logs.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


def start_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    open_browser_flag: bool = True,
    reload: bool = False,
) -> None:
    """
    Start the web server and optionally open browser.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to listen on (default: 8080)
        open_browser_flag: Whether to automatically open browser
        reload: Enable auto-reload for development
    """
    import uvicorn

    url = f"http://{host}:{port}"

    print(f"\n{'='*60}")
    print("  Jira Migration Tool - Web GUI")
    print(f"{'='*60}")
    print(f"\n  Server starting at: {url}")
    print(f"  API docs available at: {url}/docs")

    if is_wsl():
        print("\n  WSL detected - browser will open in Windows")

    print("\n  Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")

    if open_browser_flag:
        # Delay browser opening to allow server startup
        Timer(1.5, open_browser, [url]).start()

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


def main() -> int:
    """Main entry point for the web GUI."""
    try:
        start_server()
        return 0
    except KeyboardInterrupt:
        print("\nServer stopped.")
        return 0
    except Exception as e:
        logger.exception("Failed to start web server")
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
