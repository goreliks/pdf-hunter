import cv2
import numpy as np
from PIL import Image
from pyzbar import pyzbar
from urllib.parse import urlparse
import fitz  # PyMuPDF
import io
from typing import Optional, Dict
from pydantic import BaseModel, Field


def has_qr_code(image_path):
    """
    Quick check if image has QR codes (without decoding)
    Returns: True/False
    """
    try:
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
            if image is None:
                print(f"Warning: Could not load image from path: {image_path}")
                return False
        else:
            image = cv2.cvtColor(np.array(image_path), cv2.COLOR_RGB2BGR)
        
        detector = cv2.QRCodeDetector()
        retval, _ = detector.detect(image)
        return retval
    except Exception as e:
        print(f"Error checking for QR codes: {e}")
        return False


def extract_qr_urls(image_path):
    """
    Extract URLs from QR codes using pyzbar
    Returns: list of URLs
    """
    # Load image
    if isinstance(image_path, str):
        pil_image = Image.open(image_path)
    else:
        pil_image = image_path
    
    # Convert to numpy array
    image_np = np.array(pil_image)
    
    # Decode QR codes
    qr_codes = pyzbar.decode(image_np)
    
    urls = []
    for qr in qr_codes:
        try:
            data = qr.data.decode('utf-8')
            if is_valid_url(data):
                urls.append(data)
        except UnicodeDecodeError:
            continue
    
    return urls


def is_valid_url(text):
    """Check if text is a valid URL"""
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception:
        return False


def process_pdf_for_qr_codes(pdf_path, specific_pages=None):
    """
    Process PDF pages for QR codes
    Args:
        pdf_path: Path to the PDF file
        specific_pages: List of 0-based page numbers to process. If None, processes all pages.
    Returns: list of dictionaries with page numbers and URLs
    """
    doc = fitz.open(pdf_path)
    results = []
    
    # If specific_pages is provided, use it. Otherwise, process all pages.
    pages_to_process = specific_pages if specific_pages is not None else range(len(doc))
    
    for page_num in pages_to_process:
        # Validate page number
        if page_num < 0 or page_num >= len(doc):
            print(f"Warning: Page {page_num} is out of range. Skipping.")
            continue
            
        page = doc.load_page(page_num)
        
        # Convert page to image (good quality for QR detection)
        mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for crisp QR codes
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        # Check for QR codes
        if has_qr_code(image):
            print(f"Page {page_num}: QR detected, extracting URLs...")
            urls = extract_qr_urls(image)
            
            if urls:
                for url in urls:
                    results.append({
                        'url': url,
                        'page_number': page_num,
                        'url_type': 'extracted_from_qr',
                        'is_external': True
                    })
                print(f"  Found: {urls}")
            else:
                print(f"  No valid URLs found")
        else:
            print(f"Page {page_num}: No QR codes")
    
    doc.close()
    return results


def check_single_image(image_path):
    """Check a single image for QR codes"""
    if has_qr_code(image_path):
        print("QR code detected!")
        urls = extract_qr_urls(image_path)
        if urls:
            print(f"URLs found: {urls}")
            return urls
        else:
            print("QR code found but no valid URLs")
            return []
    else:
        print("No QR codes detected")
        return []

# Example usage
if __name__ == "__main__":
    import os
    
    print("QR Extraction Module - Testing imports and basic functionality")

    test_image_path = "./tests/qrmonkey.jpg"
    print(f"\nTesting with image: {test_image_path}")
    urls = check_single_image(test_image_path)
    
    # For PDF
    results = process_pdf_for_qr_codes("./tests/hello_qr.pdf", specific_pages=[0, 1])
    print(f"\nQR URLs extracted from PDF: {results}")