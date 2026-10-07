from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from all pages of a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text as a single string.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the PDF contains no extractable text.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    reader = PdfReader(str(path))

    extracted_pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            extracted_pages.append(page_text)

    extracted_text = "\n\n".join(extracted_pages).strip()

    if not extracted_text:
        raise ValueError(
            "No extractable text was found in the PDF."
        )

    return extracted_text