import base64
from PIL import Image
import io
import pathlib
import os
from datetime import datetime

from .schemas import PreprocessingState, PDFHashData, ExtractedImage, ExtractedURL


from pdf_hunter.shared.utils.hashing import calculate_file_hashes
from pdf_hunter.shared.utils.image_extraction import extract_pages_as_base64_images, calculate_image_phash, get_pdf_page_count, save_image
from pdf_hunter.shared.utils.url_extraction import extract_urls_from_pdf
from pdf_hunter.shared.utils.file_operations import ensure_output_directory
from pdf_hunter.shared.utils.qr_extraction import process_pdf_for_qr_codes


def setup_session(state: PreprocessingState):
    """
    Initializes the PDF extraction by validating paths, calculating hashes,
    generating session_id, and creating session-specific directory structure.
    """
    print("--- PDF Extraction: Setting Up Session ---")
    try:
        file_path = state['file_path']
        base_output_directory = state.get('output_directory', 'output')
        number_of_pages_to_process = state["number_of_pages_to_process"]

        # 1. Calculate file hashes first (needed for session_id)
        hashes = calculate_file_hashes(file_path)
        pdf_hash = PDFHashData(sha1=hashes["sha1"], md5=hashes["md5"])

        # 2. Generate session_id using {sha1}_{timestamp}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{pdf_hash.sha1}_{timestamp}"

        # 3. Create session-specific output directory
        session_output_directory = os.path.join(base_output_directory, session_id)
        preprocessing_directory = os.path.join(session_output_directory, "preprocessing")

        # 4. Ensure directories exist
        ensure_output_directory(pathlib.Path(session_output_directory))
        ensure_output_directory(pathlib.Path(preprocessing_directory))

        # 5. Get total page count
        page_count = get_pdf_page_count(file_path)

        # 6. Indices of pages to process
        pages_to_process = list(range(number_of_pages_to_process))

        print(f"Session ID: {session_id}")
        print(f"PDF Hash (SHA1): {pdf_hash.sha1}")
        print(f"Session Output Directory: {session_output_directory}")
        print(f"Total Pages: {page_count}")

        return {
            "session_id": session_id,
            "output_directory": session_output_directory,  # Update to session-specific directory
            "pdf_hash": pdf_hash,
            "page_count": page_count,
            "pages_to_process": pages_to_process
        }

    except Exception as e:
        error_msg = f"Error during initialization: {e}"
        print(f"[ERROR] {error_msg}")
        return {"errors": [error_msg]}


def extract_pdf_images(state: PreprocessingState):
    """
    Extracts images from the specified pages of the PDF, calculates their
    perceptual hash (phash), and saves them to the preprocessing subdirectory.
    """
    print("--- PDF Extraction: Extracting PDF Images ---")
    try:
        file_path = state['file_path']
        session_output_dir = state['output_directory']
        preprocessing_dir = pathlib.Path(os.path.join(session_output_dir, "preprocessing"))
        pages_to_process = state.get('pages_to_process')

        # If specific pages aren't defined, default to the first page.
        if not pages_to_process:
            pages_to_process = [0] if state.get('page_count', 0) > 0 else []

        # 1. Extract raw image data using our utility
        base64_images_data = extract_pages_as_base64_images(
            pdf_path=file_path,
            pages=pages_to_process,
            dpi=150,
            image_format="PNG"
        )

        extracted_images = []
        for img_data in base64_images_data:
            # 2. Decode image to calculate phash and save
            img_bytes = base64.b64decode(img_data["base64_data"])
            pil_image = Image.open(io.BytesIO(img_bytes))

            # 3. Calculate perceptual hash
            phash = calculate_image_phash(pil_image)

            # 4. Save the image file to preprocessing subdirectory
            saved_path = save_image(
                image=pil_image,
                output_dir=preprocessing_dir,
                page_number=img_data['page_number'],
                image_format="PNG",
                phash=phash
            )

            # 5. Create the structured ExtractedImage object
            # This reflects all our schema decisions.
            extracted_image = ExtractedImage(
                page_number=img_data["page_number"],
                base64_data=img_data["base64_data"],
                image_format=img_data["image_format"],
                phash=phash,
                saved_path=str(saved_path)
            )
            extracted_images.append(extracted_image)

        print(f"Extracted and processed {len(extracted_images)} image(s).")
        return {"extracted_images": extracted_images}

    except Exception as e:
        error_msg = f"Error during image extraction: {e}"
        print(f"[ERROR] {error_msg}")
        return {"errors": [error_msg]}


def find_embedded_urls(state: PreprocessingState):
    """
    Extracts URLs from the specified pages of the PDF from both
    annotations and raw text.
    """
    print("--- PDF Extraction: Finding Embedded URLs ---")
    try:
        file_path = state['file_path']
        pages_to_process = state.get('pages_to_process')

        # If specific pages aren't defined, default to the first page.
        if not pages_to_process:
            pages_to_process = [0] if state.get('page_count', 0) > 0 else []

        # 1. Extract URL data using our final, validated utility
        url_data_list = extract_urls_from_pdf(
            pdf_path=file_path,
            specific_pages=pages_to_process
        )

        # 2. Convert the dictionaries into ExtractedURL Pydantic objects.
        # The **url_data syntax will correctly map all keys from our utility's
        # dictionary output (including 'xref') to the Pydantic model fields.
        extracted_urls = [ExtractedURL(**url_data) for url_data in url_data_list]

        print(f"Extracted {len(extracted_urls)} URL finding(s).")
        return {"extracted_urls": extracted_urls}

    except Exception as e:
        error_msg = f"Error during URL extraction: {e}"
        print(f"[ERROR] {error_msg}")
        return {"errors": [error_msg]}
    

def scan_qr_codes(state: PreprocessingState):
    """
    Extracts QR codes from the specified pages of the PDF.
    """
    print("--- PDF Extraction: Scanning QR Codes ---")
    try:
        file_path = state['file_path']
        pages_to_process = state.get('pages_to_process')

        # If specific pages aren't defined, default to the first page.
        if not pages_to_process:
            pages_to_process = [0] if state.get('page_count', 0) > 0 else []

        # 1. Extract QR code data using our utility
        qr_data_list = process_pdf_for_qr_codes(
            pdf_path=file_path,
            specific_pages=pages_to_process
        )

        # 2. Convert the dictionaries into ExtractedURL Pydantic objects.
        extracted_qr_urls = [ExtractedURL(**qr_data) for qr_data in qr_data_list]

        print(f"Extracted {len(extracted_qr_urls)} QR code URL(s).")
        return {"extracted_urls": extracted_qr_urls}

    except Exception as e:
        error_msg = f"Error during QR code extraction: {e}"
        print(f"[ERROR] {error_msg}")
        return {"errors": [error_msg]}
