"""Vercel Python runtime entry point — exposes FastAPI ASGI app."""
import sys
from pathlib import Path

# Add src/ to path so `import sequor` works without pip install -e .
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from sequor.onboarding.app import app

# Top-level ASGI app for @vercel/python runtime
application = app
