import re
from html import unescape
from pathlib import Path

from pypdf import PdfReader


def clean_extracted_text(text: str) -> str:
    """
    Normalize extracted PDF text while preserving paragraph structure.
    """

    text = unescape(text)

    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize unusual whitespace and invisible PDF characters.
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")
    text = text.replace("\u00ad", "")

    cleaned_lines = []

    for line in text.split("\n"):
        # Remove control characters except ordinary whitespace.
        line = "".join(
            character
            for character in line
            if character in "\t " or ord(character) >= 32
        )

        # Collapse repeated spaces and tabs within each line.
        line = re.sub(r"[ \t]+", " ", line).strip()

        cleaned_lines.append(line)

    # Preserve paragraph breaks, but remove excessive blank lines.
    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    return cleaned_text.strip()


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract and clean text from all pages of a PDF file.
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
            cleaned_page = clean_extracted_text(page_text)

            if cleaned_page:
                extracted_pages.append(cleaned_page)

    extracted_text = "\n\n".join(extracted_pages).strip()

    if not extracted_text:
        raise ValueError(
            "No extractable text was found in the PDF."
        )

    return extracted_text