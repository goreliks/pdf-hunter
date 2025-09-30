"""Test error handling in PDF Extraction agent."""

import asyncio
import os
from pdf_hunter.agents.pdf_extraction.graph import preprocessing_graph
from pdf_hunter.agents.pdf_extraction.schemas import PDFExtractionState


async def test_missing_file_path():
    """Test with missing PDF file path."""
    print("\n=== Test 1: Missing File Path ===")
    state = PDFExtractionState(
        pdf_path="",  # Empty file path
        session_id="test_session",
        output_directory="./output/test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        errors=[]
    )
    
    result = await preprocessing_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully with error message
    assert len(result.get('errors', [])) > 0
    print("✓ Test passed: Handles missing file path gracefully")


async def test_nonexistent_file():
    """Test with nonexistent PDF file."""
    print("\n=== Test 2: Nonexistent File ===")
    
    # Get project root
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    
    state = PDFExtractionState(
        pdf_path=os.path.join(project_root, "tests/assets/pdfs/nonexistent.pdf"),
        session_id="test_session",
        output_directory="./output/test_session",
        page_images=[],
        embedded_urls=[],
        qr_code_urls=[],
        errors=[]
    )
    
    result = await preprocessing_graph.ainvoke(state)
    print(f"Errors: {result.get('errors', [])}")
    # Should handle gracefully with error message
    assert len(result.get('errors', [])) > 0
    print("✓ Test passed: Handles nonexistent file gracefully")


async def test_negative_max_pages():
    """Test with negative MAXIMUM_PAGES_TO_PROCESS value."""
    print("\n=== Test 3: Negative Max Pages ===")
    
    # Temporarily modify the config (this is just a validation test)
    from pdf_hunter import config
    original_max = config.MAXIMUM_PAGES_TO_PROCESS
    
    try:
        # Set negative value
        config.MAXIMUM_PAGES_TO_PROCESS = -1
        
        # Get project root
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../.."))
        test_file = os.path.join(project_root, "tests/assets/pdfs/hello_qr_and_link.pdf")
        
        state = PDFExtractionState(
            pdf_path=test_file,
            session_id="test_session",
            output_directory="./output/test_session",
            page_images=[],
            embedded_urls=[],
            qr_code_urls=[],
            errors=[]
        )
        
        result = await preprocessing_graph.ainvoke(state)
        print(f"Errors: {result.get('errors', [])}")
        # Should handle gracefully with error message about invalid max pages
        assert len(result.get('errors', [])) > 0
        print("✓ Test passed: Handles negative max pages gracefully")
    finally:
        # Restore original value
        config.MAXIMUM_PAGES_TO_PROCESS = original_max


async def test_zero_max_pages():
    """Test with zero MAXIMUM_PAGES_TO_PROCESS value."""
    print("\n=== Test 4: Zero Max Pages ===")
    
    # Temporarily modify the config
    from pdf_hunter import config
    original_max = config.MAXIMUM_PAGES_TO_PROCESS
    
    try:
        # Set zero value
        config.MAXIMUM_PAGES_TO_PROCESS = 0
        
        # Get project root
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(module_dir, "../.."))
        test_file = os.path.join(project_root, "tests/assets/pdfs/hello_qr_and_link.pdf")
        
        state = PDFExtractionState(
            pdf_path=test_file,
            session_id="test_session",
            output_directory="./output/test_session",
            page_images=[],
            embedded_urls=[],
            qr_code_urls=[],
            errors=[]
        )
        
        result = await preprocessing_graph.ainvoke(state)
        print(f"Errors: {result.get('errors', [])}")
        # Should handle gracefully with error message about invalid max pages
        assert len(result.get('errors', [])) > 0
        print("✓ Test passed: Handles zero max pages gracefully")
    finally:
        # Restore original value
        config.MAXIMUM_PAGES_TO_PROCESS = original_max


async def main():
    """Run all tests."""
    print("Testing PDF Extraction Agent Error Handling")
    print("=" * 60)
    
    try:
        await test_missing_file_path()
        await test_nonexistent_file()
        await test_negative_max_pages()
        await test_zero_max_pages()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
