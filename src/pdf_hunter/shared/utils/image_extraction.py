import base64
import io
import pathlib
from typing import List, Union, Optional

import pymupdf  # PyMuPDF
from PIL import Image

try:
    import imagehash
except ImportError:
    imagehash = None # Handle optional dependency

def get_pdf_page_count(pdf_path: Union[str, pathlib.Path]) -> int:
    """Gets the total number of pages in a PDF document."""
    pdf_path = pathlib.Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    try:
        with pymupdf.open(pdf_path) as doc:
            return doc.page_count
    except Exception as e:
        raise RuntimeError(f"Could not read PDF page count from {pdf_path}: {e}")

def extract_pages_as_base64_images(
    pdf_path: Union[str, pathlib.Path],
    pages: List[int],
    dpi: int = 150,
    image_format: str = "PNG"
) -> List[dict]:
    """
    Extracts specified pages from a PDF as base64 encoded images.

    Args:
        pdf_path: Path to the PDF file.
        pages: A list of 0-based page numbers to extract.
        dpi: Resolution for the output image.
        image_format: The image format (e.g., "PNG", "JPEG").

    Returns:
        A list of dictionaries, each containing page_number, base64_data, and image_format.
    """
    pdf_path = pathlib.Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    extracted_images = []
    try:
        with pymupdf.open(pdf_path) as doc:
            for page_num in pages:
                if 0 <= page_num < doc.page_count:
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=dpi)
                    img_bytes = pix.tobytes(output=image_format.lower())
                    base64_data = base64.b64encode(img_bytes).decode('utf-8')
                    
                    extracted_images.append({
                        'page_number': page_num,
                        'base64_data': base64_data,
                        'image_format': image_format.upper()
                    })
    except Exception as e:
        raise RuntimeError(f"Error extracting images from PDF {pdf_path}: {e}")
        
    return extracted_images

def calculate_image_phash(image: Image.Image) -> Optional[str]:
    """
    Calculates the perceptual hash (phash) of a PIL Image.

    Args:
        image: A PIL Image object.

    Returns:
        The perceptual hash as a string, or None if imagehash is not installed.
    """
    if imagehash is None:
        print("[WARNING] imagehash library not installed. pHash will not be calculated. Run 'pip install imagehash'.")
        return None
    
    try:
        return str(imagehash.phash(image))
    except Exception as e:
        raise RuntimeError(f"Error calculating perceptual hash: {e}")

def save_image(
    image: Image.Image,
    output_dir: pathlib.Path,
    page_number: int,
    image_format: str = "PNG",
    phash: Optional[str] = None
) -> pathlib.Path:
    """
    Saves a PIL Image with a descriptive filename.

    Args:
        image: The PIL Image object to save.
        output_dir: The directory to save the image in.
        page_number: The page number the image came from.
        image_format: The format to save the image in.

    Returns:
        The full path to the saved image file.
    """
    # Use the output directory name as a prefix for the image file
    # to group images from the same analysis session.
    file_stem = phash if phash else output_dir.name
    filename = f"{file_stem}_page_{page_number}.{image_format.lower()}"
    output_path = output_dir / filename
    
    try:
        image.save(output_path, format=image_format.upper())
        return output_path
    except Exception as e:
        raise RuntimeError(f"Error saving image to {output_path}: {e}")
    

if __name__ == "__main__":
    file_path = "/Users/gorelik/Courses/pdf-hunter/tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    print(get_pdf_page_count(file_path))
