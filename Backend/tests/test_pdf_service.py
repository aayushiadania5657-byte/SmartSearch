import pytest

from app.services.pdf_service import (
    clean_extracted_text,
    extract_text_from_pdf,
)


def test_clean_extracted_text_decodes_html_entities():
    text = "Python&#x20;is&#x20;powerful."

    result = clean_extracted_text(text)

    assert result == "Python is powerful."


def test_clean_extracted_text_normalizes_whitespace():
    text = "Python   is\t\tuseful.\u00a0Learn more."

    result = clean_extracted_text(text)

    assert result == "Python is useful. Learn more."


def test_clean_extracted_text_preserves_paragraphs():
    text = "First paragraph.\n\nSecond paragraph."

    result = clean_extracted_text(text)

    assert result == "First paragraph.\n\nSecond paragraph."


def test_clean_extracted_text_removes_excessive_blank_lines():
    text = "First paragraph.\n\n\n\nSecond paragraph."

    result = clean_extracted_text(text)

    assert result == "First paragraph.\n\nSecond paragraph."


def test_clean_extracted_text_removes_invisible_characters():
    text = "Smart\u200bSearch\u00ad is useful."

    result = clean_extracted_text(text)

    assert result == "SmartSearch is useful."


def test_extract_text_from_pdf_rejects_missing_file(tmp_path):
    missing_file = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(str(missing_file))


def test_extract_text_from_pdf_cleans_page_text(
    tmp_path,
    monkeypatch,
):
    import app.services.pdf_service as pdf_service

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"fake pdf")

    class FakePage:
        def extract_text(self):
            return "Python&#x20;is powerful.\n\nMachine   Learning."

    class FakeReader:
        def __init__(self, file_path):
            self.pages = [FakePage()]

    monkeypatch.setattr(
        pdf_service,
        "PdfReader",
        FakeReader,
    )

    result = extract_text_from_pdf(str(pdf_file))

    assert result == (
        "Python is powerful.\n\nMachine Learning."
    )


def test_extract_text_from_pdf_rejects_empty_text(
    tmp_path,
    monkeypatch,
):
    import app.services.pdf_service as pdf_service

    pdf_file = tmp_path / "empty.pdf"
    pdf_file.write_bytes(b"fake pdf")

    class FakePage:
        def extract_text(self):
            return ""

    class FakeReader:
        def __init__(self, file_path):
            self.pages = [FakePage()]

    monkeypatch.setattr(
        pdf_service,
        "PdfReader",
        FakeReader,
    )

    with pytest.raises(
        ValueError,
        match="No extractable text",
    ):
        extract_text_from_pdf(str(pdf_file))