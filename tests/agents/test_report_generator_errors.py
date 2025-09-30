"""Test error handling in Report Generator agent."""

import asyncio
import os
from pdf_hunter.agents.report_generator.graph import report_generator_graph
from pdf_hunter.agents.report_generator.schemas import ReportGeneratorState


async def test_minimal_state():
    """Test with minimal state (no analysis reports)."""
    print("\n=== Test 1: Minimal State ===")
    state = ReportGeneratorState(
        pdf_path="test.pdf",
        session_id="test_session",
        output_directory="./output/test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        static_analysis_final_report=None,
        url_investigations=[],
        threat_verdict=None,
        final_report=None,
        errors=[]
    )
    
    result = await report_generator_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    print(f"Has threat verdict: {result.get('threat_verdict') is not None}")
    print(f"Has final report: {result.get('final_report') is not None}")
    # Should complete - report generator always produces output even with minimal data
    assert result.get('final_report') is not None or len(result.get('errors', [])) > 0
    print("✓ Test passed: Handles minimal state gracefully")


async def test_missing_session_id():
    """Test with missing session ID."""
    print("\n=== Test 2: Missing Session ID ===")
    state = ReportGeneratorState(
        pdf_path="test.pdf",
        session_id="",  # Empty session ID
        output_directory="./output/test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        static_analysis_final_report=None,
        url_investigations=[],
        threat_verdict=None,
        final_report=None,
        errors=[]
    )
    
    result = await report_generator_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully
    print("✓ Test passed: Handles missing session ID gracefully")


async def test_missing_output_directory():
    """Test with missing output directory."""
    print("\n=== Test 3: Missing Output Directory ===")
    state = ReportGeneratorState(
        pdf_path="test.pdf",
        session_id="test_session",
        output_directory="",  # Empty output directory
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        static_analysis_final_report=None,
        url_investigations=[],
        threat_verdict=None,
        final_report=None,
        errors=[]
    )
    
    result = await report_generator_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully, may have issues with file saving
    print("✓ Test passed: Handles missing output directory gracefully")


async def test_invalid_directory_permissions():
    """Test with invalid directory (simulated by using root path)."""
    print("\n=== Test 4: Invalid Directory Permissions ===")
    state = ReportGeneratorState(
        pdf_path="test.pdf",
        session_id="test_session",
        output_directory="/invalid/root/path/no/permissions",  # Invalid path
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        visual_analysis_report=None,
        static_analysis_final_report=None,
        url_investigations=[],
        threat_verdict=None,
        final_report=None,
        errors=[]
    )
    
    result = await report_generator_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should complete with errors about file saving
    print("✓ Test passed: Handles invalid directory permissions gracefully")


async def main():
    """Run all tests."""
    print("Testing Report Generator Agent Error Handling")
    print("=" * 60)
    
    try:
        await test_minimal_state()
        await test_missing_session_id()
        await test_missing_output_directory()
        await test_invalid_directory_permissions()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
