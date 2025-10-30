"""Test XMP metadata URL extraction in PDF Extraction agent."""

import asyncio
import os
from pdf_hunter.agents.pdf_extraction.graph import preprocessing_graph
from pdf_hunter.agents.pdf_extraction.schemas import PDFExtractionInputState


async def test_xmp_url_extraction():
    """Test that XMP metadata URLs are extracted by the PDF extraction agent."""
    print("\n=== Test: XMP Metadata URL Extraction ===")

    # Get project root and test file path
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    test_file = os.path.join(
        project_root,
        "tests/assets/pdfs/e24904ccd67c243801cb0ee0a9072aa9b61c51ce2d0caf32bacbd14fddb89ae7.pdf"
    )

    # Verify test file exists
    if not os.path.exists(test_file):
        print(f"✗ Test file not found: {test_file}")
        raise FileNotFoundError(f"Test file not found: {test_file}")

    print(f"Testing with file: {os.path.basename(test_file)}")

    # Create input state
    state = PDFExtractionInputState(
        file_path=test_file,
        output_directory="./output/test_xmp_extraction",
        number_of_pages_to_process=1,
        session_id="test_xmp_session"
    )

    # Run the preprocessing graph
    print("Running PDF extraction agent...")
    result = await preprocessing_graph.ainvoke(state)

    # Check for errors
    errors = result.get('errors', [])
    if errors:
        print(f"Errors during extraction: {errors}")
        raise AssertionError(f"PDF extraction failed with errors: {errors}")

    # Get extracted URLs
    extracted_urls = result.get('extracted_urls', [])
    print(f"\nTotal URLs extracted: {len(extracted_urls)}")

    # Separate content URLs from metadata URLs
    content_urls = [url for url in extracted_urls if url.url_type != "metadata"]
    metadata_urls = [url for url in extracted_urls if url.url_type == "metadata"]

    print(f"  Content URLs (annotations + text): {len(content_urls)}")
    print(f"  Metadata URLs (XMP): {len(metadata_urls)}")

    # Validate metadata URLs
    print("\nMetadata URLs extracted:")
    for url in metadata_urls:
        print(f"  - {url.url} (source: {url.source})")

    # Expected XMP URLs for this test file
    expected_xmp_urls = [
        "http://www.dynaforms.com",
        "https://www.radpdf.com",
        "https://www.pdfescape.com",
        "http://ns.adobe.com/xap/1.0/",
        "http://ns.adobe.com/xap/1.0/mm/",
        "http://ns.adobe.com/pdf/1.3/",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    ]

    # Check that we got the expected number of metadata URLs
    if len(metadata_urls) != len(expected_xmp_urls):
        print(f"\n✗ Expected {len(expected_xmp_urls)} metadata URLs, got {len(metadata_urls)}")
        raise AssertionError(f"Expected {len(expected_xmp_urls)} metadata URLs, got {len(metadata_urls)}")

    # Check that all expected URLs are present
    extracted_url_strings = [url.url for url in metadata_urls]
    missing_urls = [url for url in expected_xmp_urls if url not in extracted_url_strings]

    if missing_urls:
        print(f"\n✗ Missing expected URLs: {missing_urls}")
        raise AssertionError(f"Missing expected URLs: {missing_urls}")

    # Verify all metadata URLs have proper source attribution
    urls_without_source = [url for url in metadata_urls if not url.source]
    if urls_without_source:
        print(f"\n✗ Found metadata URLs without source attribution: {urls_without_source}")
        raise AssertionError("All metadata URLs should have source attribution")

    # Verify metadata URLs have page_number=None
    urls_with_page = [url for url in metadata_urls if url.page_number is not None]
    if urls_with_page:
        print(f"\n✗ Metadata URLs should not have page numbers: {urls_with_page}")
        raise AssertionError("Metadata URLs should have page_number=None")

    print("\n✓ All validations passed!")
    print(f"✓ Extracted all {len(expected_xmp_urls)} expected XMP metadata URLs")
    print("✓ All metadata URLs have proper source attribution")
    print("✓ All metadata URLs have url_type='metadata'")
    print("✓ All metadata URLs have page_number=None")

    return result


async def test_xmp_url_types():
    """Test that XMP URLs have correct url_type values."""
    print("\n=== Test: XMP URL Type Validation ===")

    # Get project root and test file path
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    test_file = os.path.join(
        project_root,
        "tests/assets/pdfs/e24904ccd67c243801cb0ee0a9072aa9b61c51ce2d0caf32bacbd14fddb89ae7.pdf"
    )

    state = PDFExtractionInputState(
        file_path=test_file,
        output_directory="./output/test_xmp_types",
        number_of_pages_to_process=1,
        session_id="test_xmp_types"
    )

    result = await preprocessing_graph.ainvoke(state)
    extracted_urls = result.get('extracted_urls', [])

    # Verify all URLs have a url_type field
    urls_without_type = [url for url in extracted_urls if not hasattr(url, 'url_type') or not url.url_type]
    if urls_without_type:
        print(f"✗ Found URLs without url_type: {urls_without_type}")
        raise AssertionError("All URLs should have a url_type field")

    # Verify metadata URLs are properly classified
    metadata_urls = [url for url in extracted_urls if url.url_type == "metadata"]

    # Tool URLs should be present
    tool_urls = [url for url in metadata_urls if any(domain in url.url for domain in ["dynaforms", "radpdf", "pdfescape"])]
    if len(tool_urls) != 3:
        print(f"✗ Expected 3 tool URLs, found {len(tool_urls)}")
        raise AssertionError(f"Expected 3 tool URLs in metadata, found {len(tool_urls)}")

    # Namespace URLs should be present
    namespace_urls = [url for url in metadata_urls if any(domain in url.url for domain in ["adobe.com", "w3.org"])]
    if len(namespace_urls) != 4:
        print(f"✗ Expected 4 namespace URLs, found {len(namespace_urls)}")
        raise AssertionError(f"Expected 4 namespace URLs in metadata, found {len(namespace_urls)}")

    print(f"✓ Found {len(tool_urls)} tool URLs with url_type='metadata'")
    print(f"✓ Found {len(namespace_urls)} namespace URLs with url_type='metadata'")
    print("✓ All URLs have proper url_type classification")


async def main():
    """Run all XMP extraction tests."""
    print("Testing PDF Extraction Agent XMP Integration")
    print("=" * 70)

    try:
        await test_xmp_url_extraction()
        await test_xmp_url_types()

        print("\n" + "=" * 70)
        print("All XMP integration tests passed! ✓")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
