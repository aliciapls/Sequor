"""Vercel Python runtime entry point for Sequor FastAPI app."""
import asyncio
import typing as t

async def handler(req, context):
    """Vercel Python runtime handler — routes to FastAPI ASGI app."""
    from starlette.requests import Request
    from starlette.responses import Response
    from sequor.onboarding.app import app as fastapi_app

    scope = {
        "type": "http",
        "method": req["method"],
        "path": req["path"],
        "query_string": req["query"].encode() if req.get("query") else b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in req.get("headers", {})],
        "server": ("0.0.0.0", 8000),
    }

    async def receive():
        body = req.get("body", b"")
        return {"type": "http.request", "body": body}

    send_queue: t.List[dict] = []

    async def send(message: dict) -> None:
        send_queue.append(message)

    await fastapi_app(scope, receive, send)

    # Build Response from ASGI messages
    status = 200
    headers = []
    body = b""

    for msg in send_queue:
        if msg["type"] == "http.response.start":
            status = msg["status"]
            headers = msg.get("headers", [])
        elif msg["type"] == "http.response.body":
            body += msg.get("body", b"")

    header_dict = {k.decode(): v.decode() for k, v in headers}

    return Response(content=body, status_code=status, headers=header_dict)
