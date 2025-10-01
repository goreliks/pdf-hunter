"""Test SSE sink functionality in logging_config.py"""
import asyncio
import json
from loguru import logger
from pdf_hunter.config.logging_config import (
    setup_logging,
    add_sse_client,
    remove_sse_client,
    connected_clients
)


async def test_sse_sink_basic():
    """Test that SSE sink routes messages to connected clients."""
    print("\n=== Test 1: Basic SSE Sink Routing ===")
    
    # Setup logging with SSE enabled
    session_id = "test_session_001"
    setup_logging(session_id=session_id, enable_sse=True)
    
    # Create a client queue
    client_queue = asyncio.Queue()
    add_sse_client(session_id, client_queue)
    
    # Clear any setup messages
    await asyncio.sleep(0.1)
    while not client_queue.empty():
        await client_queue.get()
    
    # Now send our test log
    logger.info("Test message", agent="TestAgent", session_id=session_id, node="test_node")
    
    # Give async sink time to process
    await asyncio.sleep(0.1)
    
    # Check if message arrived
    assert not client_queue.empty(), "Queue should have received a message"
    
    message = await client_queue.get()
    data = json.loads(message)
    
    print(f"✅ Received message: {data['record']['message']}")
    assert data["record"]["message"] == "Test message"
    assert data["record"]["extra"]["agent"] == "TestAgent"
    assert data["record"]["extra"]["session_id"] == session_id
    
    # Cleanup
    remove_sse_client(session_id, client_queue)
    print("✅ Test 1 passed!")


async def test_multiple_clients():
    """Test that multiple clients receive the same message."""
    print("\n=== Test 2: Multiple Clients ===")
    
    session_id = "test_session_002"
    setup_logging(session_id=session_id, enable_sse=True)
    
    # Create 3 client queues
    queues = [asyncio.Queue() for _ in range(3)]
    for q in queues:
        add_sse_client(session_id, q)
    
    # Clear setup messages
    await asyncio.sleep(0.1)
    for q in queues:
        while not q.empty():
            await q.get()
    
    # Send log
    logger.info("Broadcast message", agent="TestAgent", session_id=session_id)
    await asyncio.sleep(0.1)
    
    # All queues should have the message
    for i, q in enumerate(queues):
        assert not q.empty(), f"Queue {i} should have message"
        message = await q.get()
        data = json.loads(message)
        print(f"✅ Client {i+1} received: {data['record']['message']}")
    
    # Cleanup
    for q in queues:
        remove_sse_client(session_id, q)
    
    print("✅ Test 2 passed!")


async def test_session_isolation():
    """Test that messages only go to correct session clients."""
    print("\n=== Test 3: Session Isolation ===")
    
    session1 = "session_A"
    session2 = "session_B"
    
    setup_logging(enable_sse=True)
    
    # Create clients for different sessions
    queue1 = asyncio.Queue()
    queue2 = asyncio.Queue()
    
    add_sse_client(session1, queue1)
    add_sse_client(session2, queue2)
    
    # Clear setup messages
    await asyncio.sleep(0.1)
    while not queue1.empty():
        await queue1.get()
    while not queue2.empty():
        await queue2.get()
    
    # Send logs to different sessions
    logger.info("Message for A", agent="TestAgent", session_id=session1)
    logger.info("Message for B", agent="TestAgent", session_id=session2)
    
    await asyncio.sleep(0.1)
    
    # Check isolation
    msg1 = json.loads(await queue1.get())
    msg2 = json.loads(await queue2.get())
    
    assert msg1["record"]["message"] == "Message for A"
    assert msg2["record"]["message"] == "Message for B"
    
    # Queue1 should not have session2's message
    assert queue1.empty(), "Queue1 should not receive session2's messages"
    assert queue2.empty(), "Queue2 should not receive session1's messages"
    
    print("✅ Session isolation working correctly!")
    
    # Cleanup
    remove_sse_client(session1, queue1)
    remove_sse_client(session2, queue2)
    
    print("✅ Test 3 passed!")


async def test_cleanup():
    """Test that cleanup properly removes clients."""
    print("\n=== Test 4: Client Cleanup ===")
    
    session_id = "test_cleanup"
    setup_logging(enable_sse=True)
    
    queue = asyncio.Queue()
    add_sse_client(session_id, queue)
    
    assert session_id in connected_clients, "Session should be in connected_clients"
    
    remove_sse_client(session_id, queue)
    
    assert session_id not in connected_clients, "Session should be removed after last client disconnects"
    
    print("✅ Test 4 passed!")


async def main():
    """Run all tests."""
    print("🧪 Testing SSE Sink Functionality\n")
    
    try:
        await test_sse_sink_basic()
        await test_multiple_clients()
        await test_session_isolation()
        await test_cleanup()
        
        print("\n" + "="*50)
        print("✅ All SSE sink tests passed!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
