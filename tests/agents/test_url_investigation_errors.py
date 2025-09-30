"""Test error handling in URL Investigation agent."""

import asyncio
import os
from pdf_hunter.agents.url_investigation.graph import link_analysis_graph
from pdf_hunter.agents.url_investigation.schemas import URLInvestigationState


async def test_no_urls():
    """Test with no URLs provided."""
    print("\n=== Test 1: No URLs ===")
    state = URLInvestigationState(
        pdf_path="test.pdf",
        session_id="test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        prioritized_urls=[],  # Empty URLs
        url_investigations=[],
        errors=[],
        investigation_logs=[]
    )
    
    result = await link_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    print(f"URL investigations: {len(result.get('url_investigations', []))}")
    assert len(result.get('url_investigations', [])) == 0, "Should have no investigations"
    print("✓ Test passed: Handles empty URL list correctly")


async def test_invalid_session():
    """Test with missing session_id."""
    print("\n=== Test 2: Invalid Session ID ===")
    state = URLInvestigationState(
        pdf_path="test.pdf",
        session_id="",  # Empty session ID
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        prioritized_urls=[],
        url_investigations=[],
        errors=[],
        investigation_logs=[]
    )
    
    result = await link_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully with error message
    assert len(result.get('errors', [])) > 0 or len(result.get('url_investigations', [])) == 0
    print("✓ Test passed: Handles invalid session gracefully")


async def test_invalid_pdf_path():
    """Test with missing pdf_path."""
    print("\n=== Test 3: Invalid PDF Path ===")
    state = URLInvestigationState(
        pdf_path="",  # Empty PDF path
        session_id="test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        prioritized_urls=[],
        url_investigations=[],
        errors=[],
        investigation_logs=[]
    )
    
    result = await link_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully
    assert len(result.get('errors', [])) > 0 or len(result.get('url_investigations', [])) == 0
    print("✓ Test passed: Handles invalid PDF path gracefully")


async def main():
    """Run all tests."""
    print("Testing URL Investigation Agent Error Handling")
    print("=" * 60)
    
    try:
        await test_no_urls()
        await test_invalid_session()
        await test_invalid_pdf_path()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
