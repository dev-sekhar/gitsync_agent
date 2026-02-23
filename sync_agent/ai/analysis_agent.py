"""
analysis_agent.py — AI Diff Analysis Agent

Responsibility: Translate raw git diffs into human-readable summaries using
Gemini. Reads GEMINI_API_KEY from .env via python-dotenv.

Agent contract:
  - analyze_diff() always returns a string (never raises to the caller).
  - On empty diff, returns a clear "fully synchronized" message immediately.
  - On Gemini error, returns a graceful fallback string.
  - Every call is audited via audit_agent.
"""
from __future__ import annotations

import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from sync_agent.utils.audit_agent import log_action

AGENT_NAME = "AnalysisAgent"

# Load .env from project root (three levels up from this file)
_ENV_PATH = Path(__file__).parents[3] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

_api_key = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=_api_key)

_MODEL = "gemini-2.0-flash"


def analyze_diff(diff: str) -> str:
    """
    Summarize a git diff using Gemini.

    Returns a 2-3 sentence human-friendly description.
    On empty diff: returns a "fully synchronized" message immediately.
    On API error: returns a graceful error string (never raises).
    """
    if not diff or diff.strip() == "":
        msg = "No changes detected. Local and remote are perfectly synchronized."
        log_action("Diff Analysis", "Success",
                   {"note": "no diff to analyse"}, agent=AGENT_NAME)
        return msg

    try:
        model = genai.GenerativeModel(_MODEL)
        prompt = (
            "Summarize the following git diff in a human-friendly way. "
            "Focus on what was changed, added, or removed. "
            "Keep it concise (2-3 sentences).\n\nDIFF:\n" + diff
        )
        response = model.generate_content(prompt)
        summary = response.text or "Could not generate summary."
        log_action("Diff Analysis", "Success",
                   {"summaryLength": len(summary)}, agent=AGENT_NAME)
        return summary

    except Exception as exc:
        log_action("Diff Analysis", "Failure",
                   {"error": str(exc)}, agent=AGENT_NAME)
        return "Error generating AI summary."
