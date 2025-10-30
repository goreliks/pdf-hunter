"""Test the get_xmp_metadata tool for file_analysis agent."""

import asyncio
import os
from pdf_hunter.agents.file_analysis.tools import get_xmp_metadata


async def test_xmp_metadata_extraction():
    """Test that get_xmp_metadata extracts XMP data from PDF."""
    print("\n=== Test: XMP Metadata Extraction ===")

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

    # Call the tool directly
    print("Calling get_xmp_metadata tool...")
    result = await asyncio.to_thread(get_xmp_metadata.invoke, {"pdf_file_path": test_file})

    print("\nTool output:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    # Validate the output contains expected sections
    if "Document Provenance:" not in result:
        print("✗ Missing provenance summary section")
        raise AssertionError("Tool output should include provenance summary")

    if "Full XMP XML:" not in result:
        print("✗ Missing full XMP metadata section")
        raise AssertionError("Tool output should include full XMP metadata")

    # Validate expected fields are present
    expected_fields = [
        "Creator Tool:",
        "Producer:",
        "XMP Toolkit:",
        "Created:",
        "Modified:"
    ]

    missing_fields = []
    for field in expected_fields:
        if field not in result:
            missing_fields.append(field)

    if missing_fields:
        print(f"✗ Missing expected fields: {missing_fields}")
        raise AssertionError(f"Tool output missing expected fields: {missing_fields}")

    # Validate expected tool URLs are present
    expected_tools = [
        "dynaforms.com",
        "radpdf.com",
        "pdfescape.com"
    ]

    missing_tools = []
    for tool in expected_tools:
        if tool not in result:
            missing_tools.append(tool)

    if missing_tools:
        print(f"✗ Missing expected tool URLs: {missing_tools}")
        raise AssertionError(f"Tool output missing expected tools: {missing_tools}")

    print("\n✓ Tool output includes provenance summary section")
    print("✓ Tool output includes full XMP metadata section")
    print("✓ All expected provenance fields present")
    print("✓ All expected tool URLs present")


async def test_xmp_tool_chain_detection():
    """Test that the tool provides data needed to identify multi-tool chains."""
    print("\n=== Test: Tool Chain Data Provision ===")

    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    test_file = os.path.join(
        project_root,
        "tests/assets/pdfs/e24904ccd67c243801cb0ee0a9072aa9b61c51ce2d0caf32bacbd14fddb89ae7.pdf"
    )

    result = await asyncio.to_thread(get_xmp_metadata.invoke, {"pdf_file_path": test_file})

    # Check that all three different tools are present
    expected_tools = ["PDFescape", "RAD PDF", "DynaPDF"]
    missing_tools = []
    for tool in expected_tools:
        if tool not in result:
            missing_tools.append(tool)

    if missing_tools:
        print(f"✗ Missing tools: {missing_tools}")
        raise AssertionError(f"Tool should show all tools in chain: {missing_tools}")

    # Check that timestamps are present for LLM to analyze
    if "2020-08-09T14:40:50Z" not in result:
        print("✗ Missing creation timestamp")
        raise AssertionError("Tool should provide creation timestamp")

    if "2020-08-09T14:57:08Z" not in result:
        print("✗ Missing modification timestamp")
        raise AssertionError("Tool should provide modification timestamp")

    print("✓ Tool provides all 3 tools in chain for LLM analysis")
    print("✓ Tool provides creation timestamp for delta calculation")
    print("✓ Tool provides modification timestamp for delta calculation")


async def test_xmp_namespace_urls():
    """Test that namespace URLs are included in XMP metadata."""
    print("\n=== Test: XMP Namespace URLs ===")

    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    test_file = os.path.join(
        project_root,
        "tests/assets/pdfs/e24904ccd67c243801cb0ee0a9072aa9b61c51ce2d0caf32bacbd14fddb89ae7.pdf"
    )

    result = await asyncio.to_thread(get_xmp_metadata.invoke, {"pdf_file_path": test_file})

    # Check for Adobe namespace URLs
    expected_namespaces = [
        "http://ns.adobe.com/xap/1.0/",
        "http://ns.adobe.com/pdf/1.3/",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    ]

    missing_namespaces = []
    for namespace in expected_namespaces:
        if namespace not in result:
            missing_namespaces.append(namespace)

    if missing_namespaces:
        print(f"✗ Missing expected namespace URLs: {missing_namespaces}")
        raise AssertionError(f"Tool output missing expected namespaces: {missing_namespaces}")

    print("✓ All expected Adobe namespace URLs present")
    print("✓ W3C RDF namespace URL present")


async def test_xmp_no_metadata():
    """Test tool behavior with PDF that has no XMP metadata."""
    print("\n=== Test: No XMP Metadata ===")

    # Use a simple test file that likely doesn't have XMP metadata
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "../.."))
    test_file = os.path.join(
        project_root,
        "tests/assets/pdfs/hello_qr_and_link.pdf"
    )

    if not os.path.exists(test_file):
        print(f"⚠️ Skipping test - file not found: {test_file}")
        return

    result = await asyncio.to_thread(get_xmp_metadata.invoke, {"pdf_file_path": test_file})

    print("\nTool output for file without XMP:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    # Tool should gracefully handle missing XMP
    if "[ERROR]" in result or "Exception" in result:
        print("✗ Tool should handle missing XMP gracefully")
        raise AssertionError("Tool should not raise errors for files without XMP metadata")

    # Should indicate no metadata found (various possible messages)
    no_metadata_indicators = [
        "No XMP metadata found",
        "/Metadata object not found",
        "not XML format",
        "[INFO]"
    ]

    has_indicator = any(indicator in result for indicator in no_metadata_indicators)
    if not has_indicator:
        print("✗ Tool should clearly indicate when XMP is absent")
        raise AssertionError("Tool should report absence of XMP metadata")

    print("✓ Tool gracefully handles files without XMP metadata")
    print("✓ Tool provides clear message about missing metadata")


async def main():
    """Run all XMP tool tests."""
    print("Testing File Analysis XMP Metadata Tool")
    print("=" * 70)

    try:
        await test_xmp_metadata_extraction()
        await test_xmp_tool_chain_detection()
        await test_xmp_namespace_urls()
        await test_xmp_no_metadata()

        print("\n" + "=" * 70)
        print("All XMP tool tests passed! ✓")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
