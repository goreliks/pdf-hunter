import re
from typing import List, Dict, Any, Union, Tuple
import pathlib

import pymupdf # PyMuPDF

def _clean_and_validate_url(url: str) -> Union[str, None]:
    """
    Internal helper to clean, normalize, and validate a URL string.
    This is a critical step to ensure data quality.

    Args:
        url: The raw URL string extracted from the PDF.

    Returns:
        A cleaned, valid URL string, or None if the URL is invalid.
    """
    url = url.strip()
    
    # Remove common trailing punctuation that isn't part of the URL
    url = re.sub(r'[.,;:!?]+$', '', url)

    # Normalize the scheme. If a URL doesn't have one, it's often not a
    # real link. We make an exception for 'www.' which is a common convention.
    if not re.match(r'^[a-zA-Z]+://', url):
        if url.startswith('www.'):
            url = 'http://' + url
        else:
            # If it's not a standard scheme and doesn't start with www,
            # we discard it as a likely false positive.
            return None

    # A final simple check for a plausible domain structure.
    # This helps filter out noise like 'ACME.PROD.V1'.
    if '.' not in url.split('://', 1)[-1]:
        return None
        
    return url

def extract_urls_from_pdf(
    pdf_path: Union[str, pathlib.Path],
    specific_pages: List[int]
) -> List[Dict[str, Any]]:
    """
    Extracts URLs from both annotations and text on specified pages of a PDF.
    This definitive version uses a sophisticated deduplication strategy to capture
    all unique findings (e.g., the same URL as both an annotation and text).

    Args:
        pdf_path: Path to the PDF file.
        specific_pages: A list of 0-based page numbers to process.

    Returns:
        A list of dictionaries, where each dictionary represents a unique URL finding.
    """
    pdf_path = pathlib.Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    # This robust regex is borrowed from the class-based implementation for better matching.
    url_pattern = re.compile(
        r'(?:(?:https?|ftp|ftps)://|www\.)'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)', re.IGNORECASE
    )
    
    all_findings = []

    try:
        with pymupdf.open(pdf_path) as doc:
            for page_num in specific_pages:
                if not (0 <= page_num < doc.page_count):
                    continue

                page = doc.load_page(page_num)
                
                # 1. Gather URLs from annotations (most reliable source)
                for link in page.get_links():
                    # Correctly check for external links using the 'kind' attribute
                    if link.get("kind") == pymupdf.LINK_URI and "uri" in link:
                        cleaned_url = _clean_and_validate_url(link["uri"])
                        if cleaned_url:
                            all_findings.append({
                                "url": cleaned_url,
                                "page_number": page_num,
                                "url_type": "annotation",
                                "coordinates": {
                                    "x0": link["from"].x0, "y0": link["from"].y0,
                                    "x1": link["from"].x1, "y1": link["from"].y1
                                },
                                "is_external": True,
                                "xref": link.get("xref")
                            })

                # 2. Gather URLs from raw text
                text = page.get_text("text")
                for match in url_pattern.finditer(text):
                    cleaned_url = _clean_and_validate_url(match.group(0))
                    if cleaned_url:
                        all_findings.append({
                            "url": cleaned_url,
                            "page_number": page_num,
                            "url_type": "text",
                            "coordinates": None,
                            "is_external": True,
                            "xref": None
                        })

    except Exception as e:
        raise RuntimeError(f"Error extracting URLs from PDF {pdf_path}: {e}")

    # This logic ensures we don't discard legitimate, distinct findings of the same URL.
    final_urls = []
    seen_keys = set()

    for finding in all_findings:
        coords = finding["coordinates"]
        coords_key: Union[Tuple, None] = None
        if coords:
            coords_key = tuple(sorted(coords.items()))

        unique_key = (
            finding["url"],
            finding["url_type"],
            finding["page_number"],
            coords_key
        )

        if unique_key not in seen_keys:
            seen_keys.add(unique_key)
            final_urls.append(finding)
            
    return final_urls


if __name__ == "__main__":
    file_path = "/Users/gorelik/Courses/pdf-hunter/tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    specific_pages = [0, 1, 2, 3]
    print(extract_urls_from_pdf(file_path, specific_pages))