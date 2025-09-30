"""Test error handling in Image Analysis agent."""

import asyncio
import os
from pdf_hunter.agents.image_analysis.graph import visual_analysis_graph
from pdf_hunter.agents.image_analysis.schemas import ImageAnalysisState


async def test_no_images():
    """Test with no page images."""
    print("\n=== Test 1: No Images ===")
    state = ImageAnalysisState(
        pdf_path="test.pdf",
        session_id="test_session",
        output_directory="./output/test_session",
        page_images=[],  # Empty images list
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        errors=[]
    )
    
    result = await visual_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    print(f"Visual analysis report: {result.get('visual_analysis_report')}")
    # Should handle gracefully - may complete with no URLs found
    assert result.get('visual_analysis_report') is not None or len(result.get('errors', [])) > 0
    print("✓ Test passed: Handles no images gracefully")


async def test_missing_pdf_path():
    """Test with missing PDF path."""
    print("\n=== Test 2: Missing PDF Path ===")
    state = ImageAnalysisState(
        pdf_path="",  # Empty PDF path
        session_id="test_session",
        output_directory="./output/test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        errors=[]
    )
    
    result = await visual_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully
    assert len(result.get('errors', [])) > 0 or result.get('visual_analysis_report') is not None
    print("✓ Test passed: Handles missing PDF path gracefully")


async def test_missing_session_id():
    """Test with missing session ID."""
    print("\n=== Test 3: Missing Session ID ===")
    state = ImageAnalysisState(
        pdf_path="test.pdf",
        session_id="",  # Empty session ID
        output_directory="./output/test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        errors=[]
    )
    
    result = await visual_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully
    assert len(result.get('errors', [])) > 0 or result.get('visual_analysis_report') is not None
    print("✓ Test passed: Handles missing session ID gracefully")


async def test_invalid_output_directory():
    """Test with invalid output directory."""
    print("\n=== Test 4: Invalid Output Directory ===")
    state = ImageAnalysisState(
        pdf_path="test.pdf",
        session_id="test_session",
        output_directory="",  # Empty output directory
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        errors=[]
    )
    
    result = await visual_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully
    print("✓ Test passed: Handles invalid output directory gracefully")


async def main():
    """Run all tests."""
    print("Testing Image Analysis Agent Error Handling")
    print("=" * 60)
    
    try:
        await test_no_images()
        await test_missing_pdf_path()
        await test_missing_session_id()
        await test_invalid_output_directory()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
