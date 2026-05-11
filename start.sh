#!/bin/bash
set -e

echo "[startup] Running database migrations..."
python -c "
import asyncio
from sequor.db.database import init_db
asyncio.run(init_db())
print('[startup] Database ready.')
"

echo "[startup] Starting uvicorn..."
exec uvicorn sequor.onboarding.app:app --host 0.0.0.0 --port 8080
