FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy source first (needed for editable install via pyproject.toml)
COPY src/ src/
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080
ENTRYPOINT ["uvicorn", "sequor.onboarding.app:app", "--host", "0.0.0.0", "--port", "8080"]
