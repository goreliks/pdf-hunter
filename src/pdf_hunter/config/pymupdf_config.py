"""
PyMuPDF (fitz) Global Configuration

Suppresses non-critical MuPDF parser warnings that don't affect functionality.
These warnings appear for malformed PDFs but don't prevent processing.

Example suppressed warning:
    MuPDF error: syntax error: expected 'obj' keyword (7327 0 ?)

This is imported automatically when the pdf_hunter.config package is loaded,
ensuring consistent PyMuPDF behavior across all modules.
"""

try:
    import fitz

    # Suppress MuPDF internal errors (non-fatal warnings about PDF structure)
    # These are diagnostic messages that don't affect functionality
    fitz.JM_mupdf_show_errors = 0

    # Keep warnings disabled (already default)
    fitz.JM_mupdf_show_warnings = 0

except ImportError:
    # PyMuPDF not installed - this is handled by individual modules
    pass
