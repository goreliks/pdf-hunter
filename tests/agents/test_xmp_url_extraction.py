"""
Test XMP metadata URL extraction on specific PDF file.

This test validates the enhanced URL extraction that includes XMP metadata parsing.
The test file e24904cc...pdf contains 7 URLs in its XMP metadata that were not
extracted by the original content-only extraction logic.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from pdf_hunter.shared.utils.url_extraction import (
    extract_urls_from_xmp_metadata,
    extract_all_urls_from_pdf
)


def test_xmp_metadata_extraction():
    """Test XMP metadata URL extraction on e24904cc...pdf"""

    # Path to test file
    pdf_path = project_root / "tests/assets/pdfs/e24904ccd67c243801cb0ee0a9072aa9b61c51ce2d0caf32bacbd14fddb89ae7.pdf"

    if not pdf_path.exists():
        print(f"❌ Test file not found: {pdf_path}")
        return False

    print(f"Testing XMP metadata extraction on: {pdf_path.name}")
    print("=" * 80)

    # Extract URLs from XMP metadata only
    metadata_urls = extract_urls_from_xmp_metadata(pdf_path)

    print(f"\n📊 XMP Metadata URL Extraction Results:")
    print(f"   Total URLs found: {len(metadata_urls)}")
    print()

    if metadata_urls:
        print("   URLs extracted from XMP metadata:")
        for i, url_info in enumerate(metadata_urls, 1):
            print(f"   {i}. {url_info['url']}")
            print(f"      Source: {url_info['source']}")
            print()
    else:
        print("   ⚠️  No URLs found in XMP metadata")

    # Expected URLs based on VirusTotal analysis
    expected_urls = [
        "https://www.radpdf.com/",
        "http://www.dynaforms.com/",
        "https://www.pdfescape.com/",
        "http://ns.adobe.com/xap/1.0/",
        "http://ns.adobe.com/xap/1.0/mm/",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns",
        "http://ns.adobe.com/pdf/1.3/"
    ]

    print(f"\n✓ Expected URLs (from VirusTotal): {len(expected_urls)}")

    # Check which expected URLs were found
    found_urls = {url_info['url'] for url_info in metadata_urls}
    missing_urls = set(expected_urls) - found_urls
    extra_urls = found_urls - set(expected_urls)

    if missing_urls:
        print(f"\n⚠️  Missing URLs ({len(missing_urls)}):")
        for url in missing_urls:
            print(f"   - {url}")

    if extra_urls:
        print(f"\n📌 Additional URLs found ({len(extra_urls)}):")
        for url in extra_urls:
            print(f"   + {url}")

    if not missing_urls and not extra_urls:
        print("\n✅ All expected URLs found with exact match!")

    return len(metadata_urls) > 0


def test_comprehensive_extraction():
    """Test comprehensive extraction (content + metadata)"""

    pdf_path = project_root / "tests/assets/pdfs/e24904ccd67c243801cb0ee0a9072aa9b61c51ce2d0caf32bacbd14fddb89ae7.pdf"

    if not pdf_path.exists():
        print(f"❌ Test file not found: {pdf_path}")
        return False

    print("\n" + "=" * 80)
    print("Testing comprehensive URL extraction (content + metadata)")
    print("=" * 80)

    # Extract all URLs (content + metadata)
    all_urls = extract_all_urls_from_pdf(pdf_path, specific_pages=[0], include_metadata=True)

    content_count = len(all_urls["content_urls"])
    metadata_count = len(all_urls["metadata_urls"])
    total_count = content_count + metadata_count

    print(f"\n📊 Comprehensive Extraction Results:")
    print(f"   Content URLs (annotations + text): {content_count}")
    print(f"   Metadata URLs (XMP): {metadata_count}")
    print(f"   Total URLs: {total_count}")

    if content_count > 0:
        print(f"\n   Content URLs:")
        for i, url_info in enumerate(all_urls["content_urls"], 1):
            print(f"   {i}. {url_info['url']} (type: {url_info['url_type']}, page: {url_info['page_number']})")
    else:
        print("\n   ℹ️  No URLs found in page content (expected for this PDF)")

    if metadata_count > 0:
        print(f"\n   Metadata URLs:")
        for i, url_info in enumerate(all_urls["metadata_urls"], 1):
            print(f"   {i}. {url_info['url']} (source: {url_info['source']})")

    return metadata_count > 0


def main():
    print("XMP Metadata URL Extraction Test")
    print("=" * 80)
    print()

    # Run tests
    test1_passed = test_xmp_metadata_extraction()
    test2_passed = test_comprehensive_extraction()

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"XMP Metadata Extraction: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Comprehensive Extraction: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
