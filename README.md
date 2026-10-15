
# SmartSearch

SmartSearch is a document search application designed to help users find relevant information in their documents using keyword-based and semantic search.

The project combines traditional information retrieval with semantic similarity to improve search relevance.

## Features

- **Hybrid search:** Combines keyword-based and semantic rankings using Reciprocal Rank Fusion (RRF).
- **Keyword search:** Uses BM25 ranking with title and phrase boosts.
- **Semantic search:** Uses the `all-MiniLM-L6-v2` sentence-transformer model.
- **Document management:** Create, list, retrieve, update, and delete documents through the API.
- **PDF ingestion:** Upload PDF files, extract their text, and save the resulting document in the database.
- **REST API:** Built with FastAPI and documented through interactive API documentation.
- **Automated tests:** Includes tests for search behavior and API endpoints.

## Technology Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Sentence Transformers
- NumPy
- PyPDF
- Pytest

## Project Structure
SmartSearch/
|-- Backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- models/
|   |   `-- search/
|   |-- tests/
|   |-- main.py
|   |-- requirements.txt
|   `-- requirements-dev.txt
|-- data/
|-- docs/
|-- frontend/
|-- .gitignore
`-- README.md

## Prerequisites

- Python 3.10 or a compatible Python version
- Git
- PowerShell on Windows, or an equivalent terminal

## Installation

Open a terminal in the project root.

### 1. Create a virtual environment

```powershell
py -3.10 -m venv .venv
```

### 2. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```powershell
python -m pip install -r Backend/requirements-dev.txt
```

## Run the Backend

From the project root, run:

```powershell
cd Backend
python -m uvicorn main:app --reload
```

The API will be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Alternative API documentation: `http://127.0.0.1:8000/redoc`

Keep the terminal running while using the API. Press `Ctrl+C` to stop the server.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/documents` | Create a document |
| POST | `/documents/upload-pdf` | Upload a PDF |
| GET | `/documents` | List documents |
| GET | `/documents/{id}` | Retrieve a document |
| PUT | `/documents/{id}` | Update a document |
| DELETE | `/documents/{id}` | Delete a document |
| GET | `/search` | Search documents |

Use the interactive API documentation at `/docs` to inspect request schemas and try the endpoints.

## Run Tests

From the project root:

```powershell
python -m pytest Backend/tests -v
```

The test suite covers keyword search, semantic search, hybrid ranking, and API behavior.

## Search Approach

SmartSearch uses a hybrid retrieval pipeline:

1. **Keyword retrieval:** BM25 ranks documents using query terms, with additional boosts for title matches and phrases.
2. **Semantic retrieval:** Sentence Transformers generate embeddings to identify semantically related text.
3. **Hybrid ranking:** Reciprocal Rank Fusion (RRF) combines keyword and semantic rankings.

Search results include relevance scores and the ranks assigned by each retrieval method. The system aims to find useful documents even when their wording differs from the query.

## Project Status

SmartSearch is under active development. Features, testing, documentation, and the frontend may evolve as development continues.

## Future Improvements

Potential improvements include:

- A polished search interface
- Better document preview and search-result highlighting
- Retrieval-augmented generation (RAG), where appropriate
- More comprehensive integration and performance testing
- Deployment and production-readiness improvements

## License

No license has been specified yet.
