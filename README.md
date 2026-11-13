
# SmartSearch

**A private, intelligent document search engine powered by hybrid information retrieval.**

SmartSearch helps users find relevant information across their documents using a combination of traditional keyword retrieval and semantic similarity. It combines BM25, Sentence Transformers, and Reciprocal Rank Fusion (RRF) to retrieve relevant documents—even when the wording of a search query differs from the document.

The project includes a React-based web interface, a FastAPI backend, PDF text extraction, and automated tests.

## Features

### Search and Retrieval
- **Hybrid search:** Combines keyword and semantic search using Reciprocal Rank Fusion (RRF).
- **Keyword search:** Uses BM25 ranking with title and phrase boosts.
- **Semantic search:** Uses the `all-MiniLM-L6-v2` Sentence Transformers model.
- **Search snippets:** Displays relevant passages from matching documents.
- **Search highlighting:** Highlights matching query terms in results.
- **Sorting:** Sorts results by relevance or title.

### Document Management
- Create, list, retrieve, update, and delete documents through the REST API.
- Upload PDF files and extract their text automatically.
- Validate PDF uploads, enforce a file-size limit, and generate unique stored filenames.

### Web Interface
- React and TypeScript frontend.
- Search workspace and document listing.
- Backend connection status indicator.
- Responsive dark-themed interface.

### Engineering and Testing
- FastAPI REST API.
- SQLAlchemy database integration.
- SQLite for local development.
- Automated tests for API endpoints, search algorithms, PDF processing, and PDF uploads.

## Technology Stack

| Area | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React, TypeScript, Vite |
| Database | SQLite, SQLAlchemy |
| Keyword retrieval | BM25 |
| Semantic retrieval | Sentence Transformers, NumPy |
| PDF processing | pypdf |
| Testing | pytest, httpx |
| Version control | Git, GitHub |

## Architecture

```text
                 USER
                  |
                  v
          React + TypeScript
            Web Interface
                  |
             REST API
                  |
                  v
           FastAPI Backend
                  |
          +-------+-------+
          |               |
          v               v
     Document          Search
     Management        Pipeline
          |               |
          v          +----+----+
       SQLite        |         |
                   BM25    Semantic
                   Search   Search
                      |         |
                      +----+----+
                           |
                           v
                    Reciprocal Rank
                      Fusion (RRF)
                           |
                           v
                    Ranked Results
```

## Project Structure

```text
SmartSearch/
|
|-- Backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- models/
|   |   |-- search/
|   |   `-- services/
|   |
|   |-- tests/
|   |-- main.py
|   |-- requirements.txt
|   `-- requirements-dev.txt
|
|-- smartsearch-ui/
|   |-- src/
|   |-- public/
|   |-- package.json
|   `-- vite.config.ts
|
|-- data/
|-- docs/
|-- .gitignore
`-- README.md
```

## Prerequisites

- Python 3.10
- Node.js
- npm
- Git

## Installation

Clone the repository:

```powershell
git clone https://github.com/aayushiadania5657-byte/SmartSearch.git
cd SmartSearch
```

### 1. Set up the Python environment

```powershell
py -3.10 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies and development tools:

```powershell
python -m pip install -r Backend/requirements-dev.txt
```

### 2. Install frontend dependencies

```powershell
cd smartsearch-ui
npm install
```

## Running the Application

SmartSearch requires two terminal sessions: one for the backend and one for the frontend.

### Terminal 1 — Backend

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1
cd Backend
python -m uvicorn main:app --reload
```

The backend runs at:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Alternative API documentation: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

### Terminal 2 — Frontend

From the project root:

```powershell
cd smartsearch-ui
npm install
npm run dev
```

Open the frontend at:

http://localhost:5173/

Keep both terminal sessions running while using the application.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API root |
| GET | `/health` | Backend health check |
| POST | `/documents` | Create a document |
| GET | `/documents` | List documents |
| GET | `/documents/{id}` | Retrieve a document |
| PUT | `/documents/{id}` | Update a document |
| DELETE | `/documents/{id}` | Delete a document |
| POST | `/documents/upload-pdf` | Upload and process a PDF |
| GET | `/search?q={query}` | Search documents |

Use the interactive API documentation at `/docs` to inspect request formats and try the endpoints.

## How Hybrid Search Works

SmartSearch uses three main retrieval stages:

**1. Keyword Retrieval — BM25**

BM25 evaluates how relevant document text is to the search query. Additional title and phrase boosts improve matching.

**2. Semantic Retrieval — Sentence Transformers**

The `all-MiniLM-L6-v2` model converts text into numerical embeddings. Semantic similarity helps identify relevant content even when documents use different wording from the query.

**3. Hybrid Ranking — Reciprocal Rank Fusion**

The two ranked result lists are combined using RRF:

\[
RRF(d) = \sum_{r \in R} \frac{1}{k + rank_r(d)}
\]

Here, `rank_r(d)` represents a document's position in a retrieval list, and `k` is a ranking constant.

The resulting documents are presented in a combined relevance order.

## Running Tests

Activate the virtual environment, then run:

```powershell
cd Backend
python -m pytest -v
```

The automated test suite covers:

- API endpoints and document operations.
- Keyword search.
- Semantic search.
- Hybrid ranking.
- PDF text extraction and cleaning.
- PDF upload validation and error handling.

## Project Status

SmartSearch is an active development project. The backend, hybrid search pipeline, PDF ingestion, React interface, and automated tests are implemented.

Further work is focused on improving reliability, search quality, user experience, deployment, and production readiness.

## Future Improvements

- Advanced search filters and pagination.
- Document preview and richer document management.
- Search evaluation using relevance metrics.
- Improved logging and application configuration.
- Database migrations.
- Deployment and production hardening.
- Retrieval-Augmented Generation (RAG), where appropriate.

## License

No open-source license has been specified yet.
