FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ src/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run migrations + start app
COPY start.sh /usr/local/bin/start
RUN chmod +x /usr/local/bin/start
ENTRYPOINT ["/usr/local/bin/start"]
