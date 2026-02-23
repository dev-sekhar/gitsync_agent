"""
server.py — Python port of server.ts
FastAPI backend exposing the same REST API the React frontend expects.
Serves the built React SPA from ./dist/ in production.

Usage:
    python server.py           # dev (auto-reload)
    uvicorn server:app --port 3000
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load GEMINI_API_KEY and any other vars from .env
load_dotenv(Path(__file__).parent / ".env")

# Agent imports
from sync_agent.core.input_agent import validate_inputs
from sync_agent.core.sync_agent import verify_sync
from sync_agent.core.update_agent import update_readme
from sync_agent.core.cleanup_agent import cleanup_local
from sync_agent.ai.analysis_agent import analyze_diff
from sync_agent.utils.audit_agent import get_logs

app = FastAPI(title="GitSync Agent API")

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class InitRequest(BaseModel):
    localPath: str
    repoUrl: str
    branch: str = "dev"


class VerifyRequest(BaseModel):
    localPath: str
    branch: str = "dev"


class UpdateReadmeRequest(BaseModel):
    localPath: str
    branch: str = "dev"
    summary: str = ""


class DeleteRequest(BaseModel):
    localPath: str
    confirmed: bool


# ---------------------------------------------------------------------------
# API Routes (mirrors server.ts endpoints exactly)
# ---------------------------------------------------------------------------

@app.get("/api/logs")
def api_get_logs():
    try:
        return get_logs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ls")
def api_ls(dir: Optional[str] = Query(default=None)):
    try:
        base = os.path.abspath(dir) if dir else os.getcwd()
        entries = list(Path(base).iterdir())
        directories = [
            {"name": e.name, "path": str(e)}
            for e in sorted(entries)
            if e.is_dir()
        ]
        return {
            "currentPath": base,
            "parentPath": str(Path(base).parent),
            "directories": directories,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/init")
def api_init(body: InitRequest):
    try:
        result = validate_inputs(body.localPath, body.repoUrl, body.branch)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/verify")
def api_verify(body: VerifyRequest):
    try:
        result = verify_sync(body.localPath, body.branch)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/update-readme")
def api_update_readme(body: UpdateReadmeRequest):
    try:
        result = update_readme(body.localPath, body.branch, body.summary)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/delete")
def api_delete(body: DeleteRequest):
    try:
        result = cleanup_local(body.localPath, body.confirmed)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Static SPA (serve built React frontend from ./dist/)
# ---------------------------------------------------------------------------

_DIST = Path(__file__).parent / "dist"

if _DIST.exists():
    # Serve static assets (JS, CSS, images …)
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """Fall-through: all non-API routes return index.html (client-side routing)."""
        index = _DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        raise HTTPException(status_code=404, detail="Frontend not built. Run: yarn build")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    print(f"Server running on http://localhost:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
