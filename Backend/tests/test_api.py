
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db
from app.models.document import Document


# Create a separate in-memory SQLite database for tests.
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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clear_search_cache():
    # Prevent search results from leaking between API tests.
    import app.api.search as search_api

    search_api._cached_engine = None
    search_api._cached_fingerprint = None

    yield

    search_api._cached_engine = None
    search_api._cached_fingerprint = None


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "SmartSearch API is running"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_empty_document_list(client):
    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "documents": [],
    }


def test_create_and_get_document(client):
    payload = {
        "title": "Python Testing Guide",
        "content": "Pytest helps test Python applications.",
        "source": "test://python-testing",
        "source_type": "web",
    }

    create_response = client.post("/documents", json=payload)

    assert create_response.status_code == 200

    created_document = create_response.json()["document"]
    document_id = created_document["id"]

    assert created_document["title"] == payload["title"]

    get_response = client.get(f"/documents/{document_id}")

    assert get_response.status_code == 200
    assert get_response.json()["content"] == payload["content"]


def test_create_document_rejects_blank_title(client):
    payload = {
        "title": "   ",
        "content": "Some useful content.",
        "source": "test://blank-title",
        "source_type": "web",
    }

    response = client.post("/documents", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Title cannot be empty"


def test_search_returns_created_document(client):
    payload = {
        "title": "Cybersecurity Best Practices",
        "content": (
            "Protect computers with strong passwords, "
            "software updates, and multi-factor authentication."
        ),
        "source": "test://cybersecurity",
        "source_type": "web",
    }

    create_response = client.post("/documents", json=payload)
    assert create_response.status_code == 200

    response = client.get(
        "/search",
        params={"q": "protect computers with strong passwords"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "protect computers with strong passwords"
    assert data["count"] >= 1
    assert data["results"][0]["title"] == "Cybersecurity Best Practices"


def test_search_rejects_missing_query(client):
    response = client.get("/search")

    assert response.status_code == 422


def test_get_missing_document_returns_404(client):
    response = client.get("/documents/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_delete_document(client):
    payload = {
        "title": "Temporary Test Document",
        "content": "This document will be deleted.",
        "source": "test://temporary",
        "source_type": "web",
    }

    create_response = client.post("/documents", json=payload)
    document_id = create_response.json()["document"]["id"]

    delete_response = client.delete(f"/documents/{document_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_document_id"] == document_id

    get_response = client.get(f"/documents/{document_id}")

    assert get_response.status_code == 404

def test_update_document(client):
    create_response = client.post(
        "/documents",
        json={
            "title": "Original Title",
            "content": "Original document content.",
            "source": "test://original",
            "source_type": "web",
        },
    )

    assert create_response.status_code == 200
    document_id = create_response.json()["document"]["id"]

    update_response = client.put(
        f"/documents/{document_id}",
        json={
            "title": "Updated Cybersecurity Guide",
            "content": (
                "Use multi-factor authentication "
                "to protect your accounts."
            ),
            "source": "test://updated",
            "source_type": "web",
        },
    )

    assert update_response.status_code == 200
    assert (
        update_response.json()["document"]["title"]
        == "Updated Cybersecurity Guide"
    )

    get_response = client.get(f"/documents/{document_id}")

    assert get_response.status_code == 200
    assert (
        get_response.json()["content"]
        == "Use multi-factor authentication to protect your accounts."
    )


def test_search_refreshes_after_document_update(client):
    create_response = client.post(
        "/documents",
        json={
            "title": "Original Gardening Guide",
            "content": "Learn how to grow tomatoes in a garden.",
            "source": "test://gardening",
            "source_type": "web",
        },
    )

    document_id = create_response.json()["document"]["id"]

    first_search = client.get(
        "/search",
        params={"q": "tomatoes garden"},
    )

    assert first_search.status_code == 200
    assert first_search.json()["count"] >= 1

    update_response = client.put(
        f"/documents/{document_id}",
        json={
            "title": "Cybersecurity Protection Guide",
            "content": (
                "Protect computers using firewalls "
                "and security updates."
            ),
            "source": "test://cybersecurity-updated",
            "source_type": "web",
        },
    )

    assert update_response.status_code == 200

    second_search = client.get(
        "/search",
        params={"q": "firewalls security updates"},
    )

    assert second_search.status_code == 200

    results = second_search.json()["results"]

    assert any(
        result["id"] == str(document_id)
        and result["title"] == "Cybersecurity Protection Guide"
        for result in results
    )
