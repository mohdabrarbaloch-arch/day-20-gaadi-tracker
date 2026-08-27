"""Vercel serverless entrypoint — re-exports the FastAPI app."""

# Vercel Python runtime looks for this module's `app` object
from app.main import app  # noqa: F401
