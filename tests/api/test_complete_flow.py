"""
Test script for complete API flow:
1. Upload PDF
2. Poll status until we get actual_session_id
3. Connect to SSE stream with actual_session_id
4. Watch logs stream in real-time
"""
import asyncio
import httpx
import json
import sys
from pathlib import Path

API_BASE = "http://localhost:8000"
TEST_PDF = Path(__file__).parent.parent / "assets" / "pdfs" / "hello_qr_and_link.pdf"


async def test_complete_flow():
    """Test the complete upload → stream → complete flow."""
    
    print("=" * 80)
    print("PDF HUNTER API - COMPLETE FLOW TEST")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Step 1: Upload PDF
        print("📤 Step 1: Uploading PDF...")
        with open(TEST_PDF, 'rb') as f:
            response = await client.post(
                f"{API_BASE}/api/analyze",
                files={"file": ("hello_qr_and_link.pdf", f, "application/pdf")},
                data={"max_pages": 2}
            )
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        temp_session_id = result["session_id"]
        print(f"✅ Upload successful!")
        print(f"   Temporary session_id: {temp_session_id}")
        print(f"   Status: {result['status']}")
        print(f"   Note: {result.get('note', 'N/A')}")
        print()
        
        # Step 2: Poll status until we get actual_session_id
        print("🔄 Step 2: Polling for actual session_id...")
        actual_session_id = None
        max_polls = 20
        poll_count = 0
        
        while poll_count < max_polls:
            await asyncio.sleep(1)
            poll_count += 1
            
            response = await client.get(f"{API_BASE}/api/sessions/{temp_session_id}/status")
            status_data = response.json()
            
            print(f"   Poll {poll_count}: status={status_data['status']}", end="")
            
            if "actual_session_id" in status_data:
                actual_session_id = status_data["actual_session_id"]
                print(f" ✅ Got actual_session_id: {actual_session_id}")
                break
            else:
                print()
        
        if not actual_session_id:
            print(f"⚠️  No actual_session_id after {max_polls} polls. Using temp session_id.")
            actual_session_id = temp_session_id
        
        print()
        
        # Step 3: Connect to SSE stream
        print(f"📡 Step 3: Connecting to SSE stream for session {actual_session_id}...")
        print("   (Showing first 30 events, then exiting)")
        print("   " + "-" * 70)
        print()
        
        event_count = 0
        max_events = 30
        
        async with client.stream(
            "GET",
            f"{API_BASE}/api/sessions/{actual_session_id}/stream",
            timeout=None
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    
                    # Parse the JSON log
                    try:
                        log_data = json.loads(line[6:])  # Skip "data: " prefix
                        record = log_data.get("record", {})
                        extra = record.get("extra", {})
                        
                        # Handle timestamp (it's a dict with 'repr' field in Loguru JSON)
                        time_info = record.get("time", {})
                        if isinstance(time_info, dict):
                            timestamp = time_info.get("repr", "")[:19]
                        else:
                            timestamp = str(time_info)[:19] if time_info else ""
                        
                        level = record.get("level", {}).get("name", "INFO")
                        agent = extra.get("agent", "unknown")
                        node = extra.get("node", "unknown")
                        message = record.get("message", "")
                        
                        # Format: timestamp | level | agent | message
                        time_part = timestamp[11:19] if len(timestamp) >= 19 else timestamp[-8:] if len(timestamp) >= 8 else timestamp
                        print(f"   [{event_count:3d}] {time_part:8s} | {level:8s} | {agent:20s} | {message[:50]}")
                        
                    except json.JSONDecodeError:
                        print(f"   [{event_count:3d}] (invalid JSON)")
                
                elif line.startswith(": keepalive"):
                    print("   💓 keepalive")
                
                if event_count >= max_events:
                    print()
                    print(f"   ✅ Received {max_events} events. Test complete!")
                    break
        
        print()
        
        # Step 4: Final status check
        print("📊 Step 4: Final status check...")
        response = await client.get(f"{API_BASE}/api/sessions/{actual_session_id}/status")
        final_status = response.json()
        
        print(f"   Status: {final_status['status']}")
        print(f"   Report available: {final_status.get('report_available', False)}")
        if "filename" in final_status:
            print(f"   Filename: {final_status['filename']}")
        
        print()
        print("=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_complete_flow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
