#!/bin/bash
# scripts/demo/start_demo.sh
# Start Sequor for PE demo — server + ngrok tunnel
# Usage: ./scripts/demo/start_demo.sh

set -e

PORT=8000
NGROK_PORT=8000

echo "═══════════════════════════════════════════════════════"
echo "  Sequor PE Demo Server"
echo "═══════════════════════════════════════════════════════"

# Check .env
if [ ! -f .env ] || ! grep -q "SENDGRID_API_KEY\|WHATSAPP_ACCESS_TOKEN" .env 2>/dev/null; then
    echo ""
    echo "⚠️  No real API keys found in .env"
    echo "   Copy .env.example to .env and fill in your keys:"
    echo "   - SENDGRID_API_KEY (for email inbound)"
    echo "   - WHATSAPP_ACCESS_TOKEN (for WhatsApp inbound)"
    echo ""
    echo "   Without real keys, you can still demo via curl (see below)."
fi

# Check ngrok
if ! command -v ngrok &> /dev/null; then
    echo "⚠️  ngrok not found. Install with: brew install ngrok"
    echo "   Then run: ngrok http $NGROK_PORT"
    echo ""
fi

# Check Ollama
echo ""
echo "[1] Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "    ✓ Ollama running at http://localhost:11434"
else
    echo "    ✗ Ollama NOT running"
    echo "    Start with: ollama serve"
fi

# Check database
echo ""
echo "[2] Checking PostgreSQL..."
if PGPASSWORD="" psql -h localhost -U postgres -d sequor -c "SELECT 1" > /dev/null 2>&1; then
    echo "    ✓ PostgreSQL connected (sequor database)"
else
    echo "    ✗ PostgreSQL not connected"
    echo "    Make sure PostgreSQL is running and database 'sequor' exists"
fi

echo ""
echo "[3] Starting FastAPI server on port $PORT..."
echo ""
cd /Users/aliciapang/Documents/GitHub/Sequor

# Start uvicorn in background
.venv/bin/python -m uvicorn sequor.onboarding.app:app \
    --host 0.0.0.0 \
    --port $PORT \
    --reload \
    > /tmp/sequor_demo_server.log 2>&1 &
SERVER_PID=$!

echo "    Server PID: $SERVER_PID"
echo "    URL: http://localhost:$PORT"
echo ""

# Wait for server to start
sleep 3

# Check if server is up
if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "    ✓ Server is up"
else
    echo "    ✗ Server failed to start"
    cat /tmp/sequor_demo_server.log
    exit 1
fi

# Start ngrok
echo ""
echo "[4] Starting ngrok tunnel..."
echo ""
ngrok http $NGROK_PORT --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 5

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || echo "")

if [ -n "$NGROK_URL" ]; then
    echo "    ✓ ngrok tunnel active"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  LIVE WEBHOOK URLs (share with groupmate):"
    echo ""
    echo "  📧 Email inbound:"
    echo "     $NGROK_URL/api/v1/email/inbound"
    echo ""
    echo "  💬 WhatsApp inbound:"
    echo "     $NGROK_URL/api/v1/whatsapp/inbound"
    echo ""
    echo "  🌐 UI: $NGROK_URL"
    echo "═══════════════════════════════════════════════════════"
else
    echo "    ⚠️  Could not get ngrok URL (may need ngrok account)"
    echo "    Sign up free at https://ngrok.com"
    echo "    Then run: ngrok http $NGROK_PORT"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Demo commands (run in another terminal):"
echo ""
echo "  # Simulate an inbound email:"
echo "  curl -X POST http://localhost:$PORT/api/v1/email/inbound \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d @scripts/demo/test_email_payload.json"
echo ""
echo "  # Simulate an inbound WhatsApp message:"
echo "  curl -X POST http://localhost:$PORT/api/v1/whatsapp/inbound \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'X-Hub-Signature-256: sha256=test' \\"
echo "    -d @scripts/demo/test_whatsapp_payload.json"
echo ""
echo "  # Run full demo script:"
echo "  python scripts/demo/run_demo.py"
echo ""
echo "  Press Ctrl+C to stop"
echo "═══════════════════════════════════════════════════════"

# Wait for interrupt
trap "echo 'Stopping...'; kill $SERVER_PID $NGROK_PID 2>/dev/null; exit" INT TERM
wait
