import base64
from PIL import Image
import io
import pathlib

from .schemas import PreprocessingState, PDFHashData, ExtractedImage, ExtractedURL


from pdf_hunter.shared.utils.hashing import calculate_file_hashes
from pdf_hunter.shared.utils.image_extraction import extract_pages_as_base64_images, calculate_image_phash, get_pdf_page_count, save_image
from pdf_hunter.shared.utils.url_extraction import extract_urls_from_pdf
from pdf_hunter.shared.utils.file_operations import ensure_output_directory
from pdf_hunter.shared.utils.qr_extraction import process_pdf_for_qr_codes


def initialization_node(state: PreprocessingState):
    """
    Initializes the preprocessing by validating paths, calculating hashes,
    and getting the total page count.
    """
    print("--- Preprocessing Node: Initializing Analysis ---")
    try:
        file_path = state['file_path']
        output_directory = state['output_directory']
        number_of_pages_to_process = state["number_of_pages_to_process"]

        # 1. Ensure output directory exists
        ensure_output_directory(pathlib.Path(output_directory))

        # 2. Calculate file hashes
        hashes = calculate_file_hashes(file_path)
        pdf_hash = PDFHashData(sha1=hashes["sha1"], md5=hashes["md5"])

        # 3. Get total page count
        page_count = get_pdf_page_count(file_path)

        # 4. Indicies of pages to process
        pages_to_process = list(range(number_of_pages_to_process))
        

        print(f"PDF Hash (SHA1): {pdf_hash.sha1}")
        print(f"Total Pages: {page_count}")

        return {
            "pdf_hash": pdf_hash,
            "page_count": page_count,
            "pages_to_process": pages_to_process
        }

    except Exception as e:
        error_msg = f"Error during initialization: {e}"
        print(f"[ERROR] {error_msg}")
        return {"errors": [error_msg]}


def image_extraction_node(state: PreprocessingState):
    """
    Extracts images from the specified pages of the PDF, calculates their
    perceptual hash (phash), and saves them to the output directory.
    """
    print("--- Preprocessing Node: Extracting Images ---")
    try:
        file_path = state['file_path']
        output_dir = pathlib.Path(state['output_directory'])
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

            # 4. Save the image file
            saved_path = save_image(
                image=pil_image,
                output_dir=output_dir,
                page_number=img_data['page_number'],
                image_format="PNG"
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


def url_extraction_node(state: PreprocessingState):
    """
    Extracts URLs from the specified pages of the PDF from both
    annotations and raw text.
    """
    print("--- Preprocessing Node: Extracting URLs ---")
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
    

def qr_extraction_node(state: PreprocessingState):
    """
    Extracts QR codes from the specified pages of the PDF.
    """
    print("--- Preprocessing Node: Extracting QR Codes ---")
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
