#!/usr/bin/env python3
"""
Manual test for SSE streaming - requires server to be running.

Run this in one terminal:
    uv run uvicorn pdf_hunter.api.server:app --port 8000

Then run this script in another terminal:
    python tests/api/test_sse_manual.py
"""
import asyncio
import json
from loguru import logger
from pdf_hunter.config.logging_config import setup_logging

# Use an existing session from output/
SESSION_ID = "ab7b10c590b66d7c3435d931c3dcada0f8ce9bff_20251001_113920"


async def test_sse_with_real_logs():
    """Test SSE by sending actual logs and verifying they stream."""
    print(f"\n🧪 Testing SSE Streaming with Real Logs")
    print(f"Session ID: {SESSION_ID}\n")
    
    # Setup logging with SSE enabled
    setup_logging(session_id=SESSION_ID, enable_sse=True)
    
    print("✅ Logging configured with SSE enabled")
    print("\nNow test with curl in another terminal:")
    print(f"  curl -N http://localhost:8000/api/sessions/{SESSION_ID}/stream\n")
    print("You should see:")
    print("  1. Historical logs from session.jsonl")
    print("  2. New logs appearing in real-time as we send them\n")
    
    input("Press Enter when curl is ready and streaming...")
    
    print("\n📤 Sending test logs...")
    
    # Send some test logs
    for i in range(5):
        logger.info(
            f"Test message {i+1} - This should appear in the SSE stream!",
            agent="TestAgent",
            session_id=SESSION_ID,
            node="manual_test",
            test_number=i+1
        )
        print(f"  Sent: Test message {i+1}")
        await asyncio.sleep(1)
    
    print("\n✅ All test messages sent!")
    print("Check your curl terminal - you should see 5 new messages appearing\n")


if __name__ == "__main__":
    asyncio.run(test_sse_with_real_logs())
