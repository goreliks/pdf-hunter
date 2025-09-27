import operator
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Annotated


class PDFHashData(BaseModel):
    """Hash information for the PDF file."""
    sha1: str = Field(..., description="SHA1 hash of the PDF file")
    md5: str = Field(..., description="MD5 hash of the PDF file")

class ExtractedImage(BaseModel):
    """Information about an extracted image."""
    page_number: int = Field(..., description="Page number the image was extracted from (0-based)")
    base64_data: str = Field(..., description="Base64-encoded image data")
    image_format: str = Field(..., description="Image format (e.g., 'png', 'jpg')")
    phash: Optional[str] = Field(None, description="Perceptual hash of the image")
    saved_path: Optional[str] = Field(None, description="Path where the image was saved")
    image_sha1: Optional[str] = Field(None, description="SHA1 hash of the image data")

class ExtractedURL(BaseModel):
    """Information about an extracted URL."""
    url: str = Field(..., description="The extracted URL")
    page_number: int = Field(..., description="Page number where the URL was found")
    url_type: str = Field(..., description="Type of URL (e.g., 'annotation', 'text')")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Coordinates of the URL if from an annotation")
    is_external: Optional[bool] = Field(None, description="Whether the URL is external")
    xref: Optional[int] = Field(None, description="The PDF cross-reference number of the link annotation object")


class PreprocessingState(TypedDict):
    """
    State for the PDF Preprocessing agent.
    Manages the extraction of visual and structural data from a PDF.
    """
    # --- Inputs ---
    file_path: str
    output_directory: str
    pages_to_process: Optional[List[int]] # List of 0-based page numbers to process
    number_of_pages_to_process: int
    session_id: Optional[str]  # Added for session management

    # --- Outputs ---
    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]
    extracted_images: List[ExtractedImage]
    extracted_urls: Annotated[List[ExtractedURL], operator.add]

    # --- Error Tracking ---
    # Using Annotated with operator.add allows LangGraph to automatically
    # aggregate errors from parallel nodes, just like in static_analysis.
    errors: Annotated[List[str], operator.add]


class PreprocessingInputState(TypedDict):
    file_path: str
    output_directory: str
    number_of_pages_to_process: int
    session_id: Optional[str]  # Added for session management


class PreprocessingOutputState(TypedDict):
    output_directory: str  # Added to pass session directory to other agents
    session_id: str        # Added to pass session ID to other agents
    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]
    pages_to_process: List[int]
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]
    errors: Annotated[List[str], operator.add]