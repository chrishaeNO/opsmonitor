"""Vercel entrypoint for the OPS Monitor FastAPI backend.

Vercel will detect this `server.py` at the repo root and run the
FastAPI app object named `app`.
"""

from backend.main import app  # FastAPI instance

