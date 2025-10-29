# PDF Extraction Agent - Technical Documentation

## Overview

The PDF Extraction agent is the **first agent** in the pdf-hunter multi-agent pipeline. It safely extracts visual and structural artifacts from PDF files without executing any content, providing the foundation for all downstream analysis.

**Position in Pipeline**: `START → PDF Extraction → {File Analysis, Image Analysis} → ...`

**Purpose**: Extract metadata, images, URLs, and QR codes from PDF files in a safe, structured manner.

## Architecture

### Graph Structure

The agent uses **LangGraph** with a parallel execution pattern:

```
START
  ↓
setup_session
  ↓ ↓ ↓ (parallel fan-out)
  extract_pdf_images
  find_embedded_urls  
  scan_qr_codes
  ↓ ↓ ↓ (convergence)
finalize_extraction
  ↓
END
```

**Implementation**: `src/pdf_hunter/agents/pdf_extraction/graph.py`

### State Management

**State Schema**: `PDFExtractionState` (TypedDict)

**Inputs**:
- `file_path` (str): Path to PDF file to analyze
- `output_directory` (str): Base output directory
- `pages_to_process` (Optional[List[int]]): Specific 0-based page numbers
- `number_of_pages_to_process` (int): How many pages to process
- `session_id` (Optional[str]): Session identifier (auto-generated if not provided)

**Outputs**:
- `pdf_hash` (PDFHashData): SHA1 and MD5 hashes of the PDF file
- `page_count` (int): Total pages in the PDF
- `extracted_images` (List[ExtractedImage]): Page images with metadata
- `extracted_urls` (List[ExtractedURL]): URLs found in the PDF (with `operator.add` for aggregation)
- `errors` (List[str]): Error messages from any failed operations

**Implementation**: `src/pdf_hunter/agents/pdf_extraction/schemas.py`

## Core Nodes

### 1. setup_session

**Purpose**: Initialize the extraction session with validation, hashing, and directory setup.

**Operations**:
1. **Input Validation**:
   - Validates file path exists and is a valid file
   - Validates `number_of_pages_to_process` is positive
   - Applies maximum page cap (MAXIMUM_PAGES_TO_PROCESS config)

2. **File Hashing**:
   - Calculates SHA1 and MD5 hashes using `calculate_file_hashes()`
   - Hashes used for file identification and session ID generation

3. **Session ID Generation**:
   - Format: `{sha1_hash}_{timestamp}`
   - Can accept pre-generated session_id or create new one
   - Ensures unique identification for each analysis run

4. **Directory Structure**:
   - Creates session-specific directory: `output/{session_id}/`
   - Creates PDF extraction subdirectory: `output/{session_id}/pdf_extraction/`
   - All extracted artifacts saved to session directories

5. **Page Count and Validation**:
   - Gets total page count from PDF using PyMuPDF
   - Validates requested pages don't exceed available pages
   - Creates list of 0-based page numbers to process

**Output**: Session metadata, validated paths, pages list

**Implementation**: `src/pdf_hunter/agents/pdf_extraction/nodes.py::setup_session()`

### 2. extract_pdf_images

**Purpose**: Extract page images, calculate perceptual hashes, and save with intelligent naming.

**Process Flow**:

1. **Page Rendering**:
   - Uses `extract_pages_as_base64_images()` utility
   - Renders pages at 150 DPI to PNG format
   - Returns base64-encoded image data for each page

2. **Perceptual Hashing**:
   - Decodes base64 to PIL Image
   - Calculates perceptual hash (pHash) using `imagehash` library
   - pHash enables duplicate detection and similarity comparison

3. **File Saving**:
   - Saves images to `output/{session_id}/pdf_extraction/` directory
   - Filename format: `{phash}_page_{page_number}.png`
   - pHash-based naming prevents duplicates and enables quick lookups

4. **Data Structure**:
   - Creates `ExtractedImage` objects with:
     - `page_number`: 0-based page index
     - `base64_data`: Encoded image for downstream processing
     - `image_format`: Format (PNG)
     - `phash`: Perceptual hash string
     - `saved_path`: Full path to saved file

**Key Technologies**:
- **PyMuPDF (fitz)**: PDF rendering via `page.get_pixmap(dpi=150)`
- **imagehash**: Perceptual hashing via `imagehash.phash(image)`
- **Pillow (PIL)**: Image handling and manipulation

**Implementation**: 
- Node: `src/pdf_hunter/agents/pdf_extraction/nodes.py::extract_pdf_images()`
- Utilities: `src/pdf_hunter/shared/utils/image_extraction.py`

### 3. find_embedded_urls

**Purpose**: Extract URLs from both PDF annotations and raw text content.

**Extraction Strategy**:

1. **Dual Source Extraction**:
   - **Annotations**: Extracts clickable links with coordinates from PDF link annotations
   - **Text Content**: Uses regex pattern matching to find URLs in text
   - Captures both explicit links and text-based URLs

2. **URL Processing**:
   - Validates and normalizes URLs with `_clean_and_validate_url()`
   - Removes trailing punctuation (.,;:!?)
   - Adds http:// scheme for www. URLs
   - Filters out false positives (e.g., "ACME.PROD.V1")

3. **Deduplication**:
   - Sophisticated strategy using unique keys: `(url, url_type, page_number, coordinates)`
   - Preserves distinct findings (same URL as both annotation and text)
   - Prevents duplicate processing

4. **Data Structure**:
   - Creates `ExtractedURL` objects with:
     - `url`: The extracted URL string
     - `page_number`: 0-based page where found
     - `url_type`: "annotation" or "text"
     - `coordinates`: Optional dict with link position (for annotations)
     - `xref`: PDF cross-reference number (for annotations)
     - `is_external`: Boolean flag for external links

**Regex Pattern**:
```python
r'(?:(?:https?|ftp|ftps)://|www\.)'
r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
r'localhost|'
r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
r'(?::\d+)?'
r'(?:/?|[/?]\S+)'
```

**Key Technologies**:
- **PyMuPDF**: Link annotation extraction and text content access
- **Python regex**: URL pattern matching
- **Custom validation**: URL cleaning and normalization

**Implementation**:
- Node: `src/pdf_hunter/agents/pdf_extraction/nodes.py::find_embedded_urls()`
- Utilities: `src/pdf_hunter/shared/utils/url_extraction.py`

### 4. scan_qr_codes

**Purpose**: Detect QR codes in extracted PDF pages and extract embedded URLs.

**Detection Process**:

1. **QR Code Detection**:
   - Uses OpenCV's QRCodeDetector for initial detection
   - Uses pyzbar for robust QR code decoding
   - Processes each rendered page image

2. **URL Extraction**:
   - Decodes QR code data to UTF-8 strings
   - Validates if decoded data is a valid URL
   - Filters for http/https schemes only

3. **Integration**:
   - Works on the same page images extracted by `extract_pdf_images`
   - Uses `process_pdf_for_qr_codes()` utility
   - Returns list of page numbers with associated QR URLs

**Validation**:
- URL scheme must be http or https
- Must have valid netloc (domain)
- Uses `urllib.parse.urlparse` for validation

**Key Technologies**:
- **OpenCV (cv2)**: QR code detection via `cv2.QRCodeDetector()`
- **pyzbar**: Robust QR/barcode decoding
- **PyMuPDF**: Page rendering for QR scanning
- **Pillow**: Image format conversion

**Implementation**:
- Node: `src/pdf_hunter/agents/pdf_extraction/nodes.py::scan_qr_codes()`
- Utilities: `src/pdf_hunter/shared/utils/qr_extraction.py`

### 5. finalize_extraction

**Purpose**: Complete the extraction session with state serialization and final logging.

**Finalization Steps**:

1. **State Aggregation**:
   - Collects results from all parallel extraction nodes
   - Counts extracted images, URLs, and errors
   - Prepares summary statistics

2. **State Persistence**:
   - Serializes complete extraction state to JSON
   - Saves to `output/{session_id}/pdf_extraction/pdf_extraction_final_state_session_{session_id}.json`
   - Uses safe serialization that handles Pydantic models and non-serializable objects

3. **Completion Logging**:
   - Success: Logs extracted counts (images, URLs)
   - Errors: Logs warning with error count if any failures
   - Event type: `EXTRACTION_COMPLETE` or `EXTRACTION_COMPLETE_WITH_ERRORS`

**State Serialization**:
- Uses custom `dump_state_to_file()` from serializer utilities
- Handles complex nested structures
- Preserves data for debugging and downstream agents

**Implementation**: `src/pdf_hunter/agents/pdf_extraction/nodes.py::finalize_extraction()`

## Key Data Structures

### PDFHashData
```python
class PDFHashData(BaseModel):
    sha1: str  # SHA1 hash of the PDF file
    md5: str   # MD5 hash of the PDF file
```

### ExtractedImage
```python
class ExtractedImage(BaseModel):
    page_number: int           # 0-based page index
    base64_data: str          # Base64-encoded image
    image_format: str         # Image format (PNG, JPEG)
    phash: Optional[str]      # Perceptual hash
    saved_path: Optional[str] # Path to saved file
```

### ExtractedURL
```python
class ExtractedURL(BaseModel):
    url: str                           # The extracted URL
    page_number: int                   # 0-based page index
    url_type: str                      # "annotation" or "text"
    coordinates: Optional[Dict]        # Position data for annotations
    is_external: Optional[bool]        # External link flag
    xref: Optional[int]                # PDF cross-reference number
```

## Core Dependencies

### PDF Processing
- **PyMuPDF (fitz)**: Core PDF parsing, rendering, and content extraction
  - Page rendering: `page.get_pixmap(dpi=150)`
  - Link annotations: `page.get_links()`
  - Text extraction: `page.get_text()`
  - Document metadata: `doc.metadata`

### Image Processing
- **Pillow (PIL)**: Image manipulation and format conversion
  - Image decoding from bytes
  - Format conversion and saving
  
- **imagehash**: Perceptual hashing for image similarity
  - `imagehash.phash(image)` for duplicate detection
  - Returns hash as string for comparison

### Computer Vision
- **OpenCV (cv2)**: QR code detection
  - `cv2.QRCodeDetector()` for QR detection
  - Image preprocessing and format conversion
  
- **pyzbar**: QR/barcode decoding
  - `pyzbar.decode(image)` for robust QR extraction
  - Supports multiple barcode formats

### Data Validation
- **Pydantic**: Schema validation and data modeling
  - Type safety for all data structures
  - Automatic validation and serialization

## Utility Functions

### Image Extraction (`image_extraction.py`)

**get_pdf_page_count(pdf_path)**:
- Returns total page count from PDF
- Uses PyMuPDF document metadata

**extract_pages_as_base64_images(pdf_path, pages, dpi, image_format)**:
- Renders specified pages to images
- Returns list of dicts with page_number, base64_data, image_format
- Default: 150 DPI, PNG format

**calculate_image_phash(image)**:
- Calculates perceptual hash of PIL Image
- Returns hash string or None if imagehash not installed
- Optional dependency handling

**save_image(image, output_dir, page_number, image_format, phash)**:
- Saves PIL Image with phash-based filename
- Format: `{phash}_page_{page_number}.{format}`
- Returns Path object to saved file

### URL Extraction (`url_extraction.py`)

**extract_urls_from_pdf(pdf_path, specific_pages)**:
- Main URL extraction function
- Combines annotation and text-based URL extraction
- Returns list of URL dicts with deduplication
- Uses sophisticated regex pattern for text URLs

**_clean_and_validate_url(url)**:
- Internal validation and normalization
- Removes trailing punctuation
- Adds http:// for www. URLs
- Filters false positives

### QR Code Processing (`qr_extraction.py`)

**has_qr_code(image_path)**:
- Quick QR code detection check
- Returns boolean without decoding
- Uses OpenCV QRCodeDetector

**extract_qr_urls(image_path)**:
- Extracts and validates URLs from QR codes
- Uses pyzbar for decoding
- Returns list of valid http/https URLs

**process_pdf_for_qr_codes(pdf_path, specific_pages)**:
- Main QR processing function for PDFs
- Renders pages and scans for QR codes
- Returns list of dicts with page numbers and URLs

### File Operations (`file_operations.py`)

**ensure_output_directory(path)**:
- Creates directory if it doesn't exist
- Creates parent directories as needed
- Silent operation if directory exists

### Hashing (`hashing.py`)

**calculate_file_hashes(file_path)**:
- Calculates SHA1 and MD5 hashes
- Returns dict with both hash values
- Used for file identification

### Serialization (`serializer.py`)

**dump_state_to_file(state, file_path)**:
- Safe JSON serialization of complex state
- Handles Pydantic models automatically
- Handles non-serializable objects gracefully
- Creates parent directories if needed

## Configuration

**Configuration File**: `src/pdf_hunter/config/__init__.py`

**Key Settings**:
- `MAXIMUM_PAGES_TO_PROCESS`: Cap on pages to prevent resource exhaustion
- `PDF_EXTRACTION_CONFIG`: LangGraph configuration for the agent

**Default Values**:
- DPI: 150 (balance between quality and file size)
- Image Format: PNG (lossless compression)
- Default pages: First page only if not specified

## Session Management

**Session ID Format**: `{sha1_hash}_{timestamp}`

**Directory Structure**:
```
output/
└── {session_id}/
    ├── pdf_extraction/
    │   ├── {phash}_page_0.png
    │   ├── {phash}_page_1.png
    │   └── pdf_extraction_final_state_session_{session_id}.json
    └── logs/
        └── session.jsonl
```

**Benefits**:
- Unique identification per analysis
- Organized artifact storage
- Easy debugging and review
- Prevents collisions between concurrent runs

## Error Handling

**Universal Pattern**:
All node functions use comprehensive try-except blocks:

```python
try:
    # Node operations
    return {results}
except Exception as e:
    logger.exception("Error message")
    return {"errors": [error_msg]}
```

**Error Aggregation**:
- Errors collected in state using `operator.add`
- Multiple nodes can report errors independently
- Finalization node reports total error count
- Partial success supported (some nodes can fail)

**Validation**:
- Input validation at function entry
- File existence checks before processing
- Page number range validation
- Safe state access with `.get()` methods

## Logging

**Logging System**: Loguru with structured events

**Log Levels**:
- **INFO**: Normal operations, progress updates
- **DEBUG**: Detailed per-item tracking
- **SUCCESS**: Completion events
- **WARNING**: Non-critical issues
- **ERROR/EXCEPTION**: Failures with stack traces

**Event Types**:
- `AGENT_START`: Agent initialization
- `SESSION_CREATED`: Session setup complete
- `IMAGE_EXTRACTION_START/COMPLETE`: Image extraction lifecycle
- `URL_EXTRACTION_START/URLS_FOUND`: URL extraction lifecycle
- `EXTRACTION_COMPLETE`: Final completion
- `ERROR`: Error events with details

**Log Destinations**:
1. **Terminal**: Colorful human-readable (INFO+)
2. **Central Log**: `logs/pdf_hunter_YYYYMMDD.jsonl` (DEBUG+)
3. **Session Log**: `output/{session_id}/logs/session.jsonl` (DEBUG+)

## Integration with Pipeline

**Input from Orchestrator**:
```python
{
    "file_path": "/path/to/file.pdf",
    "output_directory": "output",
    "number_of_pages_to_process": 5,
    "session_id": None  # Auto-generated if not provided
}
```

**Output to Downstream Agents**:
```python
{
    "session_id": "abc123_20240101_120000",
    "output_directory": "output/abc123_20240101_120000",
    "pdf_hash": PDFHashData(...),
    "page_count": 10,
    "extracted_images": [ExtractedImage(...)],
    "extracted_urls": [ExtractedURL(...)],
    "errors": []
}
```

**Downstream Usage**:
- **File Analysis**: Uses pdf_hash, file_path for static analysis
- **Image Analysis**: Uses extracted_images for visual deception detection
- **URL Investigation**: Uses extracted_urls for link reconnaissance
- **Report Generator**: Uses all metadata for comprehensive reporting

## Performance Considerations

**Optimization Strategies**:

1. **Parallel Execution**:
   - Image extraction, URL extraction, and QR scanning run in parallel
   - Reduces total execution time
   - LangGraph manages synchronization

2. **Page Limiting**:
   - MAXIMUM_PAGES_TO_PROCESS prevents resource exhaustion
   - Configurable based on system capabilities
   - Automatic capping with logging

3. **Efficient Storage**:
   - Base64 encoding for in-memory processing
   - pHash-based filenames prevent duplicates
   - PNG format balances quality and size

4. **Caching Opportunities**:
   - File hashes enable cache lookups
   - pHash enables image deduplication
   - Session directories enable result reuse

**Resource Usage**:
- **Memory**: Proportional to page count and image size
- **Disk**: ~1-2MB per page image at 150 DPI
- **CPU**: Image rendering and hashing are CPU-intensive
- **I/O**: File operations for saving images and state

## CLI Interface

**Command**: `uv run python -m pdf_hunter.agents.pdf_extraction.graph`

**Arguments**:
- `--file, -f`: PDF file to extract from (default: hello_qr_and_link.pdf)
- `--pages, -p`: Number of pages to process (default: 1)
- `--output, -o`: Output directory (default: output/pdf_extraction_results)
- `--debug`: Enable debug logging to terminal

**Example Usage**:
```bash
# Default test file
uv run python -m pdf_hunter.agents.pdf_extraction.graph

# Specific file
uv run python -m pdf_hunter.agents.pdf_extraction.graph --file test.pdf

# Multiple pages with debug
uv run python -m pdf_hunter.agents.pdf_extraction.graph --file test.pdf --pages 5 --debug
```

## Testing

**Test Coverage**: `tests/agents/test_pdf_extraction.py`

**Test Cases**:
- Missing file handling
- Invalid paths
- Empty results
- Page count validation
- Hash calculation
- Parallel execution
- Error aggregation

**Test Assets**: `tests/assets/pdfs/`
- hello_qr_and_link.pdf: Multi-feature test PDF
- Various malicious samples for comprehensive testing

## Future Enhancements

**Potential Improvements**:
1. **OCR Integration**: Text extraction from image-based PDFs
2. **Metadata Extraction**: Author, creation date, modification tracking
3. **Embedded File Detection**: Detect attached files without extraction
4. **Form Field Analysis**: Extract form field data and JavaScript
5. **Advanced QR Features**: QR code version detection, error correction level
6. **Image Enhancement**: Pre-processing for better QR detection
7. **Parallel Page Processing**: Further parallelization within nodes
8. **Progressive Results**: Stream results as pages complete

## Summary

The PDF Extraction agent provides a **safe, comprehensive, and efficient** foundation for PDF analysis:

✅ **Multi-Source Extraction**: Images, URLs (annotations + text), QR codes
✅ **Intelligent Naming**: pHash-based filenames enable deduplication
✅ **Parallel Processing**: Concurrent extraction for performance
✅ **Session Management**: Organized output with unique identifiers
✅ **Error Resilience**: Comprehensive error handling with partial success
✅ **State Persistence**: Complete state serialization for debugging
✅ **Structured Logging**: Detailed event tracking across multiple destinations

The agent successfully balances **safety** (no content execution), **completeness** (multiple extraction methods), and **performance** (parallel processing) to provide downstream agents with rich, structured data for threat analysis.
