import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db
import app.api.documents as documents_api


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()




@pytest.fixture
def client(tmp_path, monkeypatch):
    Base.metadata.create_all(bind=test_engine)

    # Redirect uploaded files to a temporary test directory.
    fake_project_root = (
        tmp_path / "project"
    )

    fake_api_file = (
        fake_project_root
        / "Backend"
        / "app"
        / "api"
        / "documents.py"
    )

    fake_api_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    fake_api_file.touch()

    monkeypatch.setattr(
        documents_api,
        "__file__",
        str(fake_api_file),
    )
    monkeypatch.setitem(
         app.dependency_overrides,
         get_db,
         override_get_db,
    )

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)


def test_upload_pdf_success(client, monkeypatch):
    monkeypatch.setattr(
        documents_api,
        "extract_text_from_pdf",
        lambda file_path: "Extracted PDF content for testing.",
    )

    response = client.post(
        "/documents/upload-pdf",
        files={
            "file": (
                "study_notes.pdf",
                b"%PDF-1.4 fake test content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "PDF uploaded and indexed successfully"
    )
    assert data["document"]["title"] == "study_notes"
    assert data["document"]["source_type"] == "pdf"
    assert data["document"]["content_length"] == len(
        "Extracted PDF content for testing."
    )

    stored_filename = data["document"]["source"].replace(
        "upload://",
        "",
    )

    assert stored_filename.endswith(".pdf")

    upload_directory = (
        documents_api.Path(documents_api.__file__)
        .resolve()
        .parents[3]
        / "data"
        / "raw"
    )

    assert (upload_directory / stored_filename).exists()


def test_upload_pdf_rejects_wrong_extension(client):
    response = client.post(
        "/documents/upload-pdf",
        files={
            "file": (
                "notes.txt",
                b"This is not a PDF.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only PDF files are supported"
    )


def test_upload_pdf_rejects_oversized_file(client):
    oversized_content = (
        b"x" * (documents_api.MAX_PDF_SIZE_BYTES + 1)
    )

    response = client.post(
        "/documents/upload-pdf",
        files={
            "file": (
                "large.pdf",
                oversized_content,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "PDF file exceeds the 10 MB upload limit"
    )

    upload_directory = (
        documents_api.Path(documents_api.__file__)
        .resolve()
        .parents[3]
        / "data"
        / "raw"
    )

    assert not list(upload_directory.glob("*.pdf"))


def test_upload_pdf_rejects_unreadable_pdf(
    client,
    monkeypatch,
):
    def raise_pdf_error(file_path):
        raise ValueError("Invalid PDF")

    monkeypatch.setattr(
        documents_api,
        "extract_text_from_pdf",
        raise_pdf_error,
    )

    response = client.post(
        "/documents/upload-pdf",
        files={
            "file": (
                "corrupted.pdf",
                b"not a real PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert "Unable to read this PDF" in (
        response.json()["detail"]
    )

    upload_directory = (
        documents_api.Path(documents_api.__file__)
        .resolve()
        .parents[3]
        / "data"
        / "raw"
    )

    assert not list(upload_directory.glob("*.pdf"))


def test_uploads_with_same_name_get_unique_storage_paths(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        documents_api,
        "extract_text_from_pdf",
        lambda file_path: "Same test content.",
    )

    first_response = client.post(
        "/documents/upload-pdf",
        files={
            "file": (
                "notes.pdf",
                b"%PDF-1.4 first",
                "application/pdf",
            )
        },
    )

    second_response = client.post(
        "/documents/upload-pdf",
        files={
            "file": (
                "notes.pdf",
                b"%PDF-1.4 second",
                "application/pdf",
            )
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_source = first_response.json()["document"]["source"]
    second_source = second_response.json()["document"]["source"]

    assert first_source != second_source
    assert first_response.json()["document"]["title"] == "notes"
    assert second_response.json()["document"]["title"] == "notes"