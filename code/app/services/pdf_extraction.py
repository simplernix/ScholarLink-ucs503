"""
PDF text extraction using PyMuPDF (imported as `fitz`).
"""
import fitz


def extract_pdf_text(file_bytes: bytes) -> str:
    """Returns the concatenated text of every page. Raises ValueError for
    bytes that aren't a readable PDF, so callers get a clear error instead
    of a confusing downstream failure."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises its own exception types
        raise ValueError("Could not read file as a PDF") from exc

    try:
        pages_text = [page.get_text() for page in doc]
    finally:
        doc.close()

    return "\n".join(pages_text).strip()
