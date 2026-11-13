
import { useEffect, useState, type FormEvent } from 'react'
import './App.css'

type SearchResult = {
  id: string
  title: string
  source: string
  snippet?: string
  score: number
  keyword_rank: number | null
  semantic_rank: number | null
}

type DocumentItem = {
  id: number
  title: string
  content: string
  source: string
  source_type: string
  created_at: string
  updated_at: string
}

const API_URL = 'http://127.0.0.1:8000'

// Escape special regular-expression characters in search terms.
function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Highlight matching query words safely using React elements.
function HighlightedText({
  text,
  query,
}: {
  text: string
  query: string
}) {
  const terms = [
    ...new Set(
      query
        .trim()
        .split(/\s+/)
        .filter((term) => term.length > 0),
    ),
  ]

  if (!text || terms.length === 0) {
    return <>{text}</>
  }

  const pattern = new RegExp(
    `(${terms.sort((a, b) => b.length - a.length).map(escapeRegExp).join('|')})`,
    'gi',
  )

  const matchingTerms = new Set(terms.map((term) => term.toLowerCase()))
  const parts = text.split(pattern)

  return (
    <>
      {parts.map((part, index) =>
        matchingTerms.has(part.toLowerCase()) ? (
          <mark className="search-highlight" key={index}>
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        ),
      )}
    </>
  )
}

function App() {
  const [query, setQuery] = useState('')
  const [activeNav, setActiveNav] = useState('Search')
  const [sortBy, setSortBy] = useState('relevance')

  const [results, setResults] = useState<SearchResult[]>([])
  const [searchedQuery, setSearchedQuery] = useState('')
  const [hasSearched, setHasSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [documentsError, setDocumentsError] = useState('')

  const [apiStatus, setApiStatus] = useState<
    'checking' | 'connected' | 'disconnected'
  >('checking')

  // Check backend health on startup and every 10 seconds.
  useEffect(() => {
    let cancelled = false

    async function checkApiHealth() {
      try {
        const response = await fetch(`${API_URL}/health`)

        if (!response.ok) {
          throw new Error('API unavailable')
        }

        const data: { status: string } = await response.json()

        if (!cancelled) {
          setApiStatus(
            data.status === 'healthy' ? 'connected' : 'disconnected',
          )
        }
      } catch {
        if (!cancelled) {
          setApiStatus('disconnected')
        }
      }
    }

    void checkApiHealth()

    const intervalId = window.setInterval(() => {
      void checkApiHealth()
    }, 10000)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [])

  // Load documents when the Documents page is opened.
  useEffect(() => {
    if (activeNav !== 'Documents') return

    let cancelled = false

    async function loadDocuments() {
      setDocumentsLoading(true)
      setDocumentsError('')

      try {
        const response = await fetch(`${API_URL}/documents`)

        if (!response.ok) {
          throw new Error(
            `Could not load documents (HTTP ${response.status})`,
          )
        }

        const data: { count: number; documents: DocumentItem[] } =
          await response.json()

        if (!cancelled) {
          setDocuments(data.documents)
        }
      } catch (err) {
        if (!cancelled) {
          setDocumentsError(
            err instanceof Error
              ? err.message
              : 'Could not load documents.',
          )
        }
      } finally {
        if (!cancelled) {
          setDocumentsLoading(false)
        }
      }
    }

    void loadDocuments()

    return () => {
      cancelled = true
    }
  }, [activeNav])

  const sortedResults = [...results].sort((a, b) =>
    sortBy === 'title'
      ? a.title.localeCompare(b.title)
      : b.score - a.score,
  )

  const sortedDocuments = [...documents].sort((a, b) =>
    sortBy === 'title'
      ? a.title.localeCompare(b.title)
      : b.updated_at.localeCompare(a.updated_at),
  )

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const searchTerm = query.trim()

    if (!searchTerm || loading) return

    setLoading(true)
    setError('')
    setHasSearched(true)
    setSearchedQuery(searchTerm)
    setResults([])
    setActiveNav('Search')

    try {
      const response = await fetch(
        `${API_URL}/search?q=${encodeURIComponent(searchTerm)}`,
      )

      if (!response.ok) {
        throw new Error(`Search failed with HTTP ${response.status}`)
      }

      const data: {
        query: string
        count: number
        results: SearchResult[]
      } = await response.json()

      setResults(data.results)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Something went wrong while searching.',
      )
    } finally {
      setLoading(false)
    }
  }

  const heading =
    activeNav === 'Search'
      ? hasSearched
        ? 'Search results'
        : 'Explore your knowledge'
      : activeNav

  let subtitle = 'Your recent searches will be available here'

  if (activeNav === 'Search') {
    subtitle = hasSearched
      ? `Results for "${searchedQuery}" · ${results.length} found`
      : 'Search your indexed documents to get started'
  } else if (activeNav === 'Documents') {
    subtitle = `${documents.length} documents in your knowledge base`
  }

  const apiStatusText = {
    checking: 'Checking API...',
    connected: 'API connected',
    disconnected: 'API disconnected',
  }[apiStatus]

  const apiStatusColor = {
    checking: '#f59e0b',
    connected: '#22c55e',
    disconnected: '#ef4444',
  }[apiStatus]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          aria-label="SmartSearch home"
          onClick={(event) => {
            event.preventDefault()
            setActiveNav('Search')
          }}
        >
          <span className="brand-icon">S</span>
          <span>SmartSearch</span>
        </a>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="nav-list" aria-label="Main navigation">
          {[
            { name: 'Search', icon: '⌕' },
            { name: 'Documents', icon: '▤' },
            { name: 'Recent', icon: '◷' },
          ].map((item) => (
            <button
              key={item.name}
              className={`nav-item ${
                activeNav === item.name ? 'active' : ''
              }`}
              onClick={() => setActiveNav(item.name)}
              type="button"
            >
              <span className="nav-icon">{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div
            className="status-dot"
            style={{ backgroundColor: apiStatusColor }}
            aria-label={apiStatus}
          />
          <div>
            <div className="status-title">Search engine</div>
            <div className="status-subtitle">{apiStatusText}</div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> {activeNav}
          </div>

          <div className="profile">
            <span className="profile-avatar">SS</span>
            <span>My workspace</span>
          </div>
        </header>

        <section className="page-content">
          <div className="welcome">
            <div className="eyebrow">
              <span className="sparkle">✳</span> YOUR KNOWLEDGE, CONNECTED
            </div>

            <h1>
              Find answers in <span>your documents.</span>
            </h1>

            <p className="welcome-copy">
              Search across your knowledge base using intelligent keyword and
              semantic search.
            </p>
          </div>

          <form className="search-form" onSubmit={handleSearch}>
            <span className="search-icon" aria-hidden="true">
              ⌕
            </span>

            <input
              aria-label="Search documents"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask a question or search your documents..."
            />

            <button
              type="submit"
              className="search-button"
              disabled={loading || !query.trim()}
            >
              {loading ? 'Searching…' : 'Search'} <span>↗</span>
            </button>
          </form>

          <div className="search-hints">
            <span>Try searching:</span>

            {['cybersecurity', 'machine learning', 'network security'].map(
              (hint) => (
                <button
                  key={hint}
                  type="button"
                  className="hint-chip"
                  onClick={() => {
                    setQuery(hint)
                    setActiveNav('Search')
                  }}
                >
                  {hint}
                </button>
              ),
            )}
          </div>

          <div className="section-heading">
            <div>
              <h2>{heading}</h2>
              <p>{subtitle}</p>
            </div>

            {((activeNav === 'Search' && results.length > 0) ||
              (activeNav === 'Documents' && documents.length > 0)) && (
              <label className="sort-control">
                <span>Sort by</span>

                <select
                  value={sortBy}
                  onChange={(event) => setSortBy(event.target.value)}
                >
                  <option value="relevance">
                    Relevance / Recently updated
                  </option>
                  <option value="title">Title</option>
                </select>
              </label>
            )}
          </div>

          {activeNav === 'Search' ? (
            loading ? (
              <div className="demo-notice" role="status">
                Searching your documents…
              </div>
            ) : error ? (
              <div className="demo-notice" role="alert">
                {error}
              </div>
            ) : sortedResults.length > 0 ? (
              <div className="results-list">
                {sortedResults.map((result, index) => (
                  <article className="result-card" key={result.id}>
                    <div className="document-icon">
                      <span>DOC</span>
                    </div>

                    <div className="result-body">
                      <div className="result-meta">
                        <span className="category">Indexed document</span>
                        <span className="meta-dot">·</span>
                        <span>{result.source}</span>
                      </div>

                      <h3>{result.title}</h3>

                      <p className="result-snippet">
                        {result.snippet ? (
                          <HighlightedText
                            text={result.snippet}
                            query={searchedQuery}
                          />
                        ) : (
                          'No text preview is available for this document.'
                        )}
                      </p>

                      <div className="result-footer">
                        <span className="match-indicator">
                          <span className="match-dot" />
                          Live API result
                        </span>

                        <span className="result-number">
                          RESULT {String(index + 1).padStart(2, '0')}
                        </span>
                      </div>

                      <div className="result-meta">
                        Keyword rank: {result.keyword_rank ?? '—'}
                        <span className="meta-dot">·</span>
                        Semantic rank: {result.semantic_rank ?? '—'}
                      </div>
                    </div>

                    <div className="result-score">
                      <span className="score-value">
                        {result.score.toFixed(6)}
                      </span>
                      <span className="score-label">RRF score</span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="demo-notice">
                {hasSearched
                  ? `No documents found for "${searchedQuery}". Try different keywords.`
                  : 'Your live search results will appear here after you search.'}
              </div>
            )
          ) : activeNav === 'Documents' ? (
            documentsLoading ? (
              <div className="demo-notice" role="status">
                Loading documents…
              </div>
            ) : documentsError ? (
              <div className="demo-notice" role="alert">
                {documentsError}
              </div>
            ) : documents.length === 0 ? (
              <div className="demo-notice">
                No documents have been added yet.
              </div>
            ) : (
              <div className="results-list">
                {sortedDocuments.map((document) => (
                  <article className="result-card" key={document.id}>
                    <div className="document-icon">
                      <span>{document.source_type.toUpperCase()}</span>
                    </div>

                    <div className="result-body">
                      <div className="result-meta">
                        <span className="category">
                          {document.source_type}
                        </span>
                        <span className="meta-dot">·</span>
                        <span>{document.source}</span>
                      </div>

                      <h3>{document.title}</h3>

                      <p>
                        {document.content.length > 180
                          ? `${document.content.slice(0, 180)}…`
                          : document.content}
                      </p>

                      <div className="result-footer">
                        <span className="match-indicator">
                          <span className="match-dot" />
                          Document ID: {document.id}
                        </span>

                        <span className="result-number">
                          UPDATED{' '}
                          {new Date(
                            document.updated_at,
                          ).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )
          ) : (
            <div className="demo-notice">
              Search history is not saved yet. Run a search to explore your
              indexed documents.
            </div>
          )}

          <footer className="page-footer">
            <span>
              SMARTSEARCH <span className="footer-separator">/</span> DOCUMENT
              DISCOVERY
            </span>
            <span>Hybrid keyword + semantic search</span>
          </footer>
        </section>
      </main>
    </div>
  )
}

export default App
