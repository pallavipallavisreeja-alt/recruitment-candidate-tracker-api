import React, { useEffect, useMemo, useState } from "react";
import {
  createCandidate,
  deleteCandidate,
  listCandidates,
  loadOpenApiSpec,
  patchCandidate,
} from "./api";

const STATUS_OPTIONS = ["applied", "screening", "interview", "offer", "hired", "rejected"];
const EMPTY_FORM = {
  name: "",
  email: "",
  skills: "",
  experience: 0,
  status: "applied",
};

function formatDate(value) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function splitSkills(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getStatusTone(status) {
  switch (status) {
    case "hired":
      return "tone-success";
    case "interview":
      return "tone-blue";
    case "offer":
      return "tone-gold";
    case "rejected":
      return "tone-danger";
    case "screening":
      return "tone-cyan";
    default:
      return "tone-muted";
  }
}

function App() {
  const [candidates, setCandidates] = useState([]);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(6);
  const [totalCount, setTotalCount] = useState(0);
  const [openApi, setOpenApi] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const selectedCandidate = useMemo(
    () => candidates.find((candidate) => candidate.id === selectedId) || null,
    [candidates, selectedId]
  );

  const totalPages = Math.max(1, Math.ceil((totalCount || 0) / pageSize));

  const stats = useMemo(() => {
    const byStatus = candidates.reduce((acc, candidate) => {
      acc[candidate.status] = (acc[candidate.status] || 0) + 1;
      return acc;
    }, {});

    return {
      total: candidates.length,
      screening: byStatus.screening || 0,
      interview: byStatus.interview || 0,
      hired: byStatus.hired || 0,
    };
  }, [candidates]);

  async function refreshCandidates() {
    setLoading(true);
    setError("");
    try {
      const response = await listCandidates({
        name: query,
        status: statusFilter || undefined,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setCandidates(response.data);
      setTotalCount(Number(response.headers.get("X-Total-Count") || response.data.length || 0));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshCandidates();
  }, [page, pageSize, query, statusFilter, sortBy, sortOrder]);

  useEffect(() => {
    loadOpenApiSpec()
      .then((response) => setOpenApi(response.data))
      .catch(() => {
        // The dashboard works without the spec, so keep this non-fatal.
      });
  }, []);

  function startCreate() {
    setSelectedId(null);
    setForm(EMPTY_FORM);
  }

  function startEdit(candidate) {
    setSelectedId(candidate.id);
    setForm({
      name: candidate.name,
      email: candidate.email,
      skills: (candidate.skills || []).join(", "),
      experience: candidate.experience,
      status: candidate.status,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    const payload = {
      name: form.name.trim(),
      email: form.email.trim(),
      skills: splitSkills(form.skills),
      experience: Number(form.experience),
      status: form.status,
    };

    try {
      if (selectedCandidate) {
        await patchCandidate(selectedCandidate.id, payload);
      } else {
        await createCandidate(payload);
      }
      setForm(EMPTY_FORM);
      setSelectedId(null);
      setPage(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(candidate) {
    const confirmed = window.confirm(`Delete ${candidate.name}?`);
    if (!confirmed) return;

    setSaving(true);
    setError("");
    try {
      await deleteCandidate(candidate.id);
      if (selectedCandidate?.id === candidate.id) {
        setSelectedId(null);
        setForm(EMPTY_FORM);
      }
      setPage(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="hero">
        <div>
          <p className="eyebrow">Intelligent API Documentation Keeper</p>
          <h1>Recruitment Candidate Tracker</h1>
          <p className="hero-copy">
            Manage candidates, inspect the generated API surface, and keep the
            documentation aligned with the backend automatically.
          </p>
        </div>

        <div className="hero-actions">
          <a className="button ghost" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            Open API Docs
          </a>
          <a className="button ghost" href="http://127.0.0.1:8000/openapi.json" target="_blank" rel="noreferrer">
            View OpenAPI JSON
          </a>
          <button className="button" onClick={startCreate} type="button">
            New Candidate
          </button>
        </div>
      </header>

      <section className="stats-grid">
        <article className="stat-card">
          <span>Total Candidates</span>
          <strong>{stats.total}</strong>
        </article>
        <article className="stat-card">
          <span>In Screening</span>
          <strong>{stats.screening}</strong>
        </article>
        <article className="stat-card">
          <span>Interview Stage</span>
          <strong>{stats.interview}</strong>
        </article>
        <article className="stat-card">
          <span>Hired</span>
          <strong>{stats.hired}</strong>
        </article>
      </section>

      <main className="layout">
        <section className="panel panel-left">
          <div className="panel-head">
            <div>
              <h2>Candidate Registry</h2>
              <p>Search, edit, and maintain candidate records.</p>
            </div>

            <div className="search-box">
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                }}
                placeholder="Filter by name"
                aria-label="Filter candidates by name"
              />
              <select
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value);
                  setPage(1);
                }}
                aria-label="Filter candidates by status"
              >
                <option value="">All statuses</option>
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </div>
            <div className="search-box">
              <select
                value={sortBy}
                onChange={(event) => {
                  setSortBy(event.target.value);
                  setPage(1);
                }}
                aria-label="Sort candidates by field"
              >
                <option value="created_at">Created at</option>
                <option value="name">Name</option>
                <option value="experience">Experience</option>
                <option value="status">Status</option>
              </select>
              <select
                value={sortOrder}
                onChange={(event) => {
                  setSortOrder(event.target.value);
                  setPage(1);
                }}
                aria-label="Sort candidates order"
              >
                <option value="desc">Newest first</option>
                <option value="asc">Oldest first</option>
              </select>
            </div>
          </div>

          {error ? <div className="alert">{error}</div> : null}

          <div className="candidate-list">
            {loading ? (
              <div className="empty-state">Loading candidates...</div>
            ) : candidates.length === 0 ? (
              <div className="empty-state">
                No candidates found. Create the first record to start tracking.
              </div>
            ) : (
              candidates.map((candidate) => (
                <article key={candidate.id} className="candidate-card">
                  <div className="candidate-top">
                    <div>
                      <h3>{candidate.name}</h3>
                      <p>{candidate.email}</p>
                    </div>
                    <span className={`status-pill ${getStatusTone(candidate.status)}`}>
                      {candidate.status}
                    </span>
                  </div>

                  <div className="meta-row">
                    <span>{candidate.experience} years experience</span>
                    <span>Created {formatDate(candidate.created_at)}</span>
                  </div>

                  <div className="skill-row">
                    {(candidate.skills || []).map((skill) => (
                      <span key={skill} className="skill-chip">
                        {skill}
                      </span>
                    ))}
                  </div>

                  <div className="card-actions">
                    <button type="button" className="secondary" onClick={() => startEdit(candidate)}>
                      Edit
                    </button>
                    <button type="button" className="danger" onClick={() => handleDelete(candidate)}>
                      Delete
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>

          <div className="pagination">
            <button
              type="button"
              className="secondary"
              disabled={page <= 1}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              Previous
            </button>

            <span>
              Page {page} of {totalPages}
            </span>

            <button
              type="button"
              className="secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            >
              Next
            </button>

            <select
              value={pageSize}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(1);
              }}
              aria-label="Page size"
            >
              <option value={6}>6 per page</option>
              <option value={10}>10 per page</option>
              <option value={20}>20 per page</option>
            </select>
          </div>
        </section>

        <aside className="panel panel-right">
          <div className="panel-head">
            <div>
              <h2>{selectedCandidate ? "Edit Candidate" : "Create Candidate"}</h2>
              <p>{selectedCandidate ? "Update the current record." : "Add a new candidate to the pipeline."}</p>
            </div>
          </div>

          <form className="candidate-form" onSubmit={handleSubmit}>
            <label>
              Full Name
              <input
                required
                minLength={2}
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="Ava Patel"
              />
            </label>

            <label>
              Email
              <input
                required
                type="email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                placeholder="ava@example.com"
              />
            </label>

            <label>
              Skills
              <textarea
                rows={4}
                value={form.skills}
                onChange={(event) => setForm({ ...form, skills: event.target.value })}
                placeholder="Python, FastAPI, SQL"
              />
            </label>

            <div className="two-col">
              <label>
                Experience
                <input
                  required
                  type="number"
                  min={0}
                  value={form.experience}
                  onChange={(event) => setForm({ ...form, experience: event.target.value })}
                />
              </label>

              <label>
                Status
                <select
                  value={form.status}
                  onChange={(event) => setForm({ ...form, status: event.target.value })}
                >
                  {STATUS_OPTIONS.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <button type="submit" className="button wide" disabled={saving}>
              {saving ? "Saving..." : selectedCandidate ? "Update Candidate" : "Create Candidate"}
            </button>

            {selectedCandidate ? (
              <button type="button" className="ghost wide" onClick={startCreate}>
                Cancel Edit
              </button>
            ) : null}
          </form>

          <section className="docs-panel">
            <div className="panel-head compact">
              <div>
                <h3>Generated API Surface</h3>
                <p>Live snapshot of the backend OpenAPI spec.</p>
              </div>
            </div>

            {openApi ? (
              <div className="docs-meta">
                <span>{Object.keys(openApi.paths || {}).length} paths</span>
                <span>{openApi.openapi}</span>
              </div>
            ) : (
              <div className="empty-state small">OpenAPI spec unavailable.</div>
            )}
          </section>
        </aside>
      </main>
    </div>
  );
}

export default App;
