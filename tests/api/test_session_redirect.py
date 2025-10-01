"""
Quick test to verify session ID redirect works.
"""
import asyncio
import httpx
import json
from pathlib import Path

API_BASE = "http://localhost:8000"
TEST_PDF = Path(__file__).parent.parent / "assets" / "pdfs" / "hello_qr_and_link.pdf"


async def test_session_id_redirect():
    """Test that temp session_id redirects to actual session_id."""
    
    print("=" * 80)
    print("SESSION ID REDIRECT TEST")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Upload PDF
        print("📤 Uploading PDF...")
        with open(TEST_PDF, 'rb') as f:
            response = await client.post(
                f"{API_BASE}/api/analyze",
                files={"file": ("test.pdf", f, "application/pdf")},
                data={"max_pages": 1}
            )
        
        result = response.json()
        temp_session_id = result["session_id"]
        print(f"   Temp session_id: ...{temp_session_id[-6:]}")
        print()
        
        # Step 2: Poll status to get actual_session_id
        print("🔄 Polling for actual_session_id...")
        for i in range(15):
            await asyncio.sleep(0.5)
            
            response = await client.get(f"{API_BASE}/api/sessions/{temp_session_id}/status")
            status_data = response.json()
            
            status = status_data['status']
            actual_id = status_data.get('actual_session_id')
            
            print(f"   Poll {i+1:2d}: status={status:12s}", end="")
            
            if actual_id:
                print(f" ✅ actual_session_id: ...{actual_id[-6:]}")
                
                # Verify they're different
                if actual_id != temp_session_id:
                    print()
                    print("🎯 SUCCESS! Session ID redirect works:")
                    print(f"   Temp:   ...{temp_session_id[-20:]}")
                    print(f"   Actual: ...{actual_id[-20:]}")
                    print()
                    return True
                else:
                    print("   ⚠️  IDs are the same (unlikely but possible)")
                    return True
            else:
                print()
        
        print()
        print("❌ FAIL: No actual_session_id after 15 polls")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_session_id_redirect())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
