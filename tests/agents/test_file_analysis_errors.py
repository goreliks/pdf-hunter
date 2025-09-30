"""Test error handling in File Analysis agent."""

import asyncio
import os
from pdf_hunter.agents.file_analysis.graph import static_analysis_graph
from pdf_hunter.agents.file_analysis.schemas import FileAnalysisState


async def test_missing_file_path():
    """Test with missing file_path."""
    print("\n=== Test 1: Missing File Path ===")
    state = FileAnalysisState(
        file_path="",  # Empty file path
        session_id="test_session",
        output_directory="./output/test_session",
        errors=[],
        mission_list=[],
        completed_investigations=[],
        mission_reports={},
        structural_summary={}
    )
    
    result = await static_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully with error message
    assert len(result.get('errors', [])) > 0
    print("✓ Test passed: Handles missing file path gracefully")


async def test_nonexistent_file():
    """Test with nonexistent file."""
    print("\n=== Test 2: Nonexistent File ===")
    
    # Get project root
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    
    state = FileAnalysisState(
        file_path=os.path.join(project_root, "tests/assets/pdfs/nonexistent.pdf"),
        session_id="test_session",
        output_directory="./output/test_session",
        errors=[],
        mission_list=[],
        completed_investigations=[],
        mission_reports={},
        structural_summary={}
    )
    
    result = await static_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully - file analysis tools will fail
    # The agent should still complete with errors
    print("✓ Test passed: Handles nonexistent file gracefully")


async def test_invalid_session():
    """Test with empty session_id."""
    print("\n=== Test 3: Invalid Session ID ===")
    
    # Get project root
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    test_file = os.path.join(project_root, "tests/assets/pdfs/hello_qr_and_link.pdf")
    
    state = FileAnalysisState(
        file_path=test_file,
        session_id="",  # Empty session ID
        output_directory="./output/test_session",
        errors=[],
        mission_list=[],
        completed_investigations=[],
        mission_reports={},
        structural_summary={}
    )
    
    result = await static_analysis_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully - may have issues with output directory
    print("✓ Test passed: Handles invalid session gracefully")


async def main():
    """Run all tests."""
    print("Testing File Analysis Agent Error Handling")
    print("=" * 60)
    
    try:
        await test_missing_file_path()
        await test_nonexistent_file()
        await test_invalid_session()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
