#!/bin/bash
# scripts/demo/send_test_message.sh
# Simulate your groupmate sending a message to your Sequor demo
# Usage: ./scripts/demo/send_test_message.sh [email|whatsapp] [routine|complex]
#
# Examples:
#   ./send_test_message.sh email routine   # Simple pricing question
#   ./send_test_message.sh whatsapp complex  # Contract negotiation
#   ./send_test_message.sh email HUMAN     # WhatsApp HUMAN override (tests escalation)

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
TYPE="${1:-email}"
SCENARIO="${2:-routine}"

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║  Sending test message — $TYPE ($SCENARIO)        ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

if [ "$TYPE" = "email" ]; then
    PAYLOAD_FILE="scripts/demo/test_email_payload.json"
    URL="$BASE_URL/api/v1/email/inbound"

    if [ "$SCENARIO" = "routine" ]; then
        # Pricing question — should be auto-answered
        echo "Scenario: Routine query (pricing question)"
        echo "Expected: AI auto-reply sent to client"
        python3 -c "
import json
p = {
    'from': 'almanie@example.com',
    'to': 'owner@integrationtest.com',
    'subject': 'Pricing question',
    'text': 'Hi! Do you offer monthly billing? Thanks!',
    'sender_ip': '203.0.113.42',
    'message_id': 'test-email-$(date +%s)',
    'date': '2026-05-05T12:00:00Z'
}
print(json.dumps(p, indent=2))
" > /tmp/email_payload.json
        PAYLOAD_FILE="/tmp/email_payload.json"

    elif [ "$SCENARIO" = "complex" ]; then
        # Contract negotiation — should escalate
        echo "Scenario: Complex query (contract negotiation)"
        echo "Expected: Escalated to backup contact with AI draft"
        python3 -c "
import json
p = {
    'from': 'almanie@example.com',
    'to': 'owner@integrationtest.com',
    'subject': 'Contract negotiation',
    'text': 'We would like to discuss custom terms for an annual contract. Can we schedule a call to negotiate pricing and SLA guarantees? This is for a 50-seat enterprise deal.',
    'sender_ip': '203.0.113.42',
    'message_id': 'test-email-$(date +%s)',
    'date': '2026-05-05T12:00:00Z'
}
print(json.dumps(p, indent=2))
" > /tmp/email_payload.json
        PAYLOAD_FILE="/tmp/email_payload.json"

    elif [ "$SCENARIO" = "HUMAN" ]; then
        # HUMAN override — forces escalation
        echo "Scenario: HUMAN override (forces escalation)"
        echo "Expected: Immediately routed to human backup"
        python3 -c "
import json
p = {
    'from': 'almanie@example.com',
    'to': 'owner@integrationtest.com',
    'subject': 'Urgent',
    'text': 'HUMAN',
    'sender_ip': '203.0.113.42',
    'message_id': 'test-email-$(date +%s)',
    'date': '2026-05-05T12:00:00Z'
}
print(json.dumps(p, indent=2))
" > /tmp/email_payload.json
        PAYLOAD_FILE="/tmp/email_payload.json"
    fi

    echo ""
    echo "→ POST $URL"
    echo ""
    RESPONSE=$(curl -s -X POST "$URL" \
        -H "Content-Type: application/json" \
        -d @"$PAYLOAD_FILE")
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

elif [ "$TYPE" = "whatsapp" ]; then
    PAYLOAD_FILE="scripts/demo/test_whatsapp_payload.json"
    URL="$BASE_URL/api/v1/whatsapp/inbound"

    if [ "$SCENARIO" = "routine" ]; then
        echo "Scenario: Routine query (pricing question)"
        echo "Expected: AI auto-reply sent via WhatsApp"
        python3 -c "
import json, time
p = {
    'object': 'whatsapp_business_account',
    'entry': [{
        'id': 'WHATSAPP_BUSINESS_ACCOUNT_ID',
        'changes': [{
            'value': {
                'messaging_product': 'whatsapp',
                'metadata': {
                    'display_phone_number': '+1234567890',
                    'phone_number_id': 'PHONE_NUMBER_ID'
                },
                'contacts': [{
                    'wa_id': '15551234567',
                    'profile': {'name': 'Almanie'}
                }],
                'messages': [{
                    'from': '15551234567',
                    'id': f'wamid.{int(time.time())}',
                    'timestamp': str(int(time.time())),
                    'type': 'text',
                    'text': {'body': 'Hi! Do you offer monthly billing?'}
                }]
            },
            'field': 'messages'
        }]
    }]
}
print(json.dumps(p, indent=2))
" > /tmp/whatsapp_payload.json
        PAYLOAD_FILE="/tmp/whatsapp_payload.json"

    elif [ "$SCENARIO" = "complex" ]; then
        echo "Scenario: Complex query (contract negotiation)"
        echo "Expected: Escalated to backup with AI draft"
        python3 -c "
import json, time
p = {
    'object': 'whatsapp_business_account',
    'entry': [{
        'id': 'WHATSAPP_BUSINESS_ACCOUNT_ID',
        'changes': [{
            'value': {
                'messaging_product': 'whatsapp',
                'metadata': {
                    'display_phone_number': '+1234567890',
                    'phone_number_id': 'PHONE_NUMBER_ID'
                },
                'contacts': [{
                    'wa_id': '15551234567',
                    'profile': {'name': 'Almanie'}
                }],
                'messages': [{
                    'from': '15551234567',
                    'id': f'wamid.{int(time.time())}',
                    'timestamp': str(int(time.time())),
                    'type': 'text',
                    'text': {'body': 'We would like to discuss custom terms for an annual contract. Can we schedule a call? 50-seat enterprise deal.'}
                }]
            },
            'field': 'messages'
        }]
    }]
}
print(json.dumps(p, indent=2))
" > /tmp/whatsapp_payload.json
        PAYLOAD_FILE="/tmp/whatsapp_payload.json"

    elif [ "$SCENARIO" = "HUMAN" ]; then
        echo "Scenario: HUMAN override (forces escalation)"
        echo "Expected: Immediately routed to human backup"
        python3 -c "
import json, time
p = {
    'object': 'whatsapp_business_account',
    'entry': [{
        'id': 'WHATSAPP_BUSINESS_ACCOUNT_ID',
        'changes': [{
            'value': {
                'messaging_product': 'whatsapp',
                'metadata': {
                    'display_phone_number': '+1234567890',
                    'phone_number_id': 'PHONE_NUMBER_ID'
                },
                'contacts': [{
                    'wa_id': '15551234567',
                    'profile': {'name': 'Almanie'}
                }],
                'messages': [{
                    'from': '15551234567',
                    'id': f'wamid.{int(time.time())}',
                    'timestamp': str(int(time.time())),
                    'type': 'text',
                    'text': {'body': 'HUMAN'}
                }]
            },
            'field': 'messages'
        }]
    }]
}
print(json.dumps(p, indent=2))
" > /tmp/whatsapp_payload.json
        PAYLOAD_FILE="/tmp/whatsapp_payload.json"
    fi

    echo ""
    echo "→ POST $URL"
    echo ""
    RESPONSE=$(curl -s -X POST "$URL" \
        -H "Content-Type: application/json" \
        -H "X-Hub-Signature-256: sha256=test" \
        -d @"$PAYLOAD_FILE")
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

else
    echo "Usage: $0 [email|whatsapp] [routine|complex|HUMAN]"
    exit 1
fi

echo ""
echo "✓ Message sent!"
echo ""
echo "Check the server logs for the full pipeline:"
echo "  tail -f /tmp/sequor_demo_server.log"
echo ""
