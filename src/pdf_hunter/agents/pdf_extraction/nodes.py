import base64
from PIL import Image
import io
import logging
import pathlib
import os
from datetime import datetime

from .schemas import PDFExtractionState, PDFHashData, ExtractedImage, ExtractedURL


from pdf_hunter.shared.utils.hashing import calculate_file_hashes
from pdf_hunter.shared.utils.image_extraction import extract_pages_as_base64_images, calculate_image_phash, get_pdf_page_count, save_image
from pdf_hunter.shared.utils.url_extraction import extract_urls_from_pdf
from pdf_hunter.shared.utils.file_operations import ensure_output_directory
from pdf_hunter.shared.utils.qr_extraction import process_pdf_for_qr_codes
from pdf_hunter.shared.utils.logging_config import get_logger

logger = get_logger(__name__)


def setup_session(state: PDFExtractionState):
    """
    Initializes the PDF extraction by validating paths, calculating hashes,
    generating session_id, and creating session-specific directory structure.
    """
    logger.info("Setting Up Session")
    try:
        file_path = state['file_path']
        base_output_directory = state.get('output_directory', 'output')
        number_of_pages_to_process = state["number_of_pages_to_process"]
        
        logger.debug(f"Processing file: {file_path}")
        logger.debug(f"Base output directory: {base_output_directory}")
        logger.debug(f"Pages to process: {number_of_pages_to_process}")

        # 1. Calculate file hashes first (needed for session_id)
        logger.debug("Calculating file hashes")
        hashes = calculate_file_hashes(file_path)
        pdf_hash = PDFHashData(sha1=hashes["sha1"], md5=hashes["md5"])

        # 2. Generate session_id using {sha1}_{timestamp}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{pdf_hash.sha1}_{timestamp}"
        logger.debug(f"Generated session ID: {session_id}")

        # 3. Create session-specific output directory
        session_output_directory = os.path.join(base_output_directory, session_id)
        pdf_extraction_directory = os.path.join(session_output_directory, "pdf_extraction")

        # 4. Ensure directories exist
        logger.debug(f"Creating directory structure in {session_output_directory}")
        ensure_output_directory(pathlib.Path(session_output_directory))
        ensure_output_directory(pathlib.Path(pdf_extraction_directory))

        # 5. Get total page count
        page_count = get_pdf_page_count(file_path)
        logger.debug(f"PDF contains {page_count} pages")

        # 6. Indices of pages to process
        pages_to_process = list(range(number_of_pages_to_process))
        
        logger.info(f"Session ID: {session_id}")
        logger.info(f"PDF Hash (SHA1): {pdf_hash.sha1}")
        logger.info(f"Session Output Directory: {session_output_directory}")
        logger.info(f"Total Pages: {page_count}")

        result = {
            "session_id": session_id,
            "output_directory": session_output_directory,  # Update to session-specific directory
            "pdf_hash": pdf_hash,
            "page_count": page_count,
            "pages_to_process": pages_to_process
        }
        logger.debug("Session setup complete")
        return result

    except Exception as e:
        error_msg = f"Error during initialization: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}


def extract_pdf_images(state: PDFExtractionState):
    """
    Extracts images from the specified pages of the PDF, calculates their
    perceptual hash (phash), and saves them to the preprocessing subdirectory.
    """
    logger.info("Extracting PDF Images")
    try:
        file_path = state['file_path']
        session_output_dir = state['output_directory']
        pdf_extraction_dir = pathlib.Path(os.path.join(session_output_dir, "pdf_extraction"))
        pages_to_process = state.get('pages_to_process')

        # If specific pages aren't defined, default to the first page.
        if not pages_to_process:
            pages_to_process = [0] if state.get('page_count', 0) > 0 else []
            logger.debug("No specific pages defined, defaulting to first page")
        else:
            logger.debug(f"Processing pages: {pages_to_process}")

        # 1. Extract raw image data using our utility
        logger.debug(f"Extracting images from {len(pages_to_process)} pages at 150 DPI")
        base64_images_data = extract_pages_as_base64_images(
            pdf_path=file_path,
            pages=pages_to_process,
            dpi=150,
            image_format="PNG"
        )

        extracted_images = []
        for img_data in base64_images_data:
            page_number = img_data['page_number']
            logger.debug(f"Processing image from page {page_number}")
            
            # 2. Decode image to calculate phash and save
            img_bytes = base64.b64decode(img_data["base64_data"])
            pil_image = Image.open(io.BytesIO(img_bytes))

            # 3. Calculate perceptual hash
            logger.debug(f"Calculating perceptual hash for page {page_number}")
            phash = calculate_image_phash(pil_image)

            # 4. Save the image file to pdf_extraction subdirectory
            logger.debug(f"Saving image for page {page_number}")
            saved_path = save_image(
                image=pil_image,
                output_dir=pdf_extraction_dir,
                page_number=page_number,
                image_format="PNG",
                phash=phash
            )

            # 5. Create the structured ExtractedImage object
            # This reflects all our schema decisions.
            extracted_image = ExtractedImage(
                page_number=page_number,
                base64_data=img_data["base64_data"],
                image_format=img_data["image_format"],
                phash=phash,
                saved_path=str(saved_path)
            )
            extracted_images.append(extracted_image)

        logger.info(f"Extracted and processed {len(extracted_images)} image(s)")
        return {"extracted_images": extracted_images}

    except Exception as e:
        error_msg = f"Error during image extraction: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}


def find_embedded_urls(state: PDFExtractionState):
    """
    Extracts URLs from the specified pages of the PDF from both
    annotations and raw text.
    """
    logger.info("Finding Embedded URLs")
    try:
        file_path = state['file_path']
        pages_to_process = state.get('pages_to_process')

        # If specific pages aren't defined, default to the first page.
        if not pages_to_process:
            pages_to_process = [0] if state.get('page_count', 0) > 0 else []
            logger.debug("No specific pages defined, defaulting to first page")
        else:
            logger.debug(f"Processing pages: {pages_to_process}")

        # 1. Extract URL data using our final, validated utility
        logger.debug("Extracting URLs from PDF")
        url_data_list = extract_urls_from_pdf(
            pdf_path=file_path,
            specific_pages=pages_to_process
        )

        # 2. Convert the dictionaries into ExtractedURL Pydantic objects.
        # The **url_data syntax will correctly map all keys from our utility's
        # dictionary output (including 'xref') to the Pydantic model fields.
        extracted_urls = [ExtractedURL(**url_data) for url_data in url_data_list]

        if logger.isEnabledFor(logging.DEBUG) and extracted_urls:
            # Log a sample URL at debug level
            sample = extracted_urls[0]
            logger.debug(f"Sample URL: {sample.url} (type: {sample.url_type}, page: {sample.page_number})")

        logger.info(f"Extracted {len(extracted_urls)} URL finding(s)")
        return {"extracted_urls": extracted_urls}

    except Exception as e:
        error_msg = f"Error during URL extraction: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}
    

def scan_qr_codes(state: PDFExtractionState):
    """
    Extracts QR codes from the specified pages of the PDF.
    """
    logger.info("Scanning QR Codes")
    try:
        file_path = state['file_path']
        pages_to_process = state.get('pages_to_process')

        # If specific pages aren't defined, default to the first page.
        if not pages_to_process:
            pages_to_process = [0] if state.get('page_count', 0) > 0 else []
            logger.debug("No specific pages defined, defaulting to first page")
        else:
            logger.debug(f"Scanning pages for QR codes: {pages_to_process}")

        # 1. Extract QR code data using our utility
        logger.debug("Processing PDF pages for QR codes")
        qr_data_list = process_pdf_for_qr_codes(
            pdf_path=file_path,
            specific_pages=pages_to_process
        )

        # 2. Convert the dictionaries into ExtractedURL Pydantic objects.
        extracted_qr_urls = [ExtractedURL(**qr_data) for qr_data in qr_data_list]

        if logger.isEnabledFor(logging.DEBUG) and extracted_qr_urls:
            # Log QR code details at debug level
            for qr_url in extracted_qr_urls:
                logger.debug(f"QR code found on page {qr_url.page_number}: {qr_url.url}")
        
        logger.info(f"Extracted {len(extracted_qr_urls)} QR code URL(s)")
        return {"extracted_urls": extracted_qr_urls}

    except Exception as e:
        error_msg = f"Error during QR code extraction: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": [error_msg]}
