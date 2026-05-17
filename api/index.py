"""Vercel Python runtime entry point — exposes FastAPI ASGI app."""
from sequor.onboarding.app import app

# Top-level ASGI app for @vercel/python runtime
application = app
