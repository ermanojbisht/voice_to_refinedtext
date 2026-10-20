#!/usr/bin/env python3
"""PWD Uttarakhand — FastAPI HTTP Service for Laravel & Web Integration.

Endpoints:
  GET  /api/translate?text=...&mode=auto
  POST /api/translate  {"text": "...", "mode": "auto"}
  GET  /api/abbreviation?q=EE
  GET  /api/abbreviations
  GET  /api/search?q=...

Run:
  python3 pwd_helper/api.py
  (or: uvicorn pwd_helper.api:app --port 8000)
"""
from __future__ import annotations

import os
import sys

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from pwd_helper.core import (
    lookup_abbreviation,
    search_abbreviations,
    list_abbreviations,
    list_by_category,
)
from pwd_helper.translator import process_input, translate

app = FastAPI(title="PWD Uttarakhand Language & Terminology API")

# Allow Laravel or any web frontend to call this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranslateRequest(BaseModel):
    text: str
    mode: Optional[str] = "auto"


@app.get("/api/translate")
def translate_get(text: str = Query(...), mode: str = Query("auto")):
    """Translate English text to Hindi or look up PWD abbreviation."""
    return process_input(text, mode=mode)


@app.post("/api/translate")
def translate_post(req: TranslateRequest):
    """Translate English text to Hindi (JSON body for Laravel Http::post)."""
    return process_input(req.text, mode=req.mode or "auto")


@app.get("/api/abbreviation")
def abbreviation_get(q: str = Query(...)):
    """Look up a single PWD abbreviation."""
    result = lookup_abbreviation(q)
    if result:
        return {"found": True, "abbreviation": q.upper().strip(), **result}
    return {"found": False, "abbreviation": q.upper().strip()}


@app.get("/api/abbreviations")
def abbreviations_list():
    """List all PWD abbreviations."""
    return list_abbreviations()


@app.get("/api/categories")
def categories_list():
    """List all abbreviations grouped by category."""
    return list_by_category()


@app.get("/api/search")
def abbreviations_search(q: str = Query(...)):
    """Search abbreviations and meanings by partial match."""
    return search_abbreviations(q)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PWD_API_PORT", 8000))
    print(f"Starting PWD Uttarakhand API on http://0.0.0.0:{port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
