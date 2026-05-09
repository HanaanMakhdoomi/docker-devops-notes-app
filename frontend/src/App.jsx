import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "https://docker-devops-notes-app.onrender.com";

const formatTime = (iso) => {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export default function App() {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [selectedNote, setSelectedNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [search, setSearch] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, setDark] = useState(false);

  const fetchNotes = async () => {
    try {
      const response = await fetch(`${API_URL}/notes`);
      const data = await response.json();
      setNotes(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const addNote = async () => {
    if (!content.trim()) return;

    setAdding(true);

    try {
      await fetch(`${API_URL}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim() || "Untitled",
          content: content.trim(),
        }),
      });

      setTitle("");
      setContent("");
      await fetchNotes();
    } finally {
      setAdding(false);
    }
  };

  const deleteNote = async (id) => {
    setDeletingId(id);

    try {
      await fetch(`${API_URL}/notes/${id}`, { method: "DELETE" });
      await fetchNotes();

      if (selectedNote?.id === id) {
        setSelectedNote(null);
      }
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, []);

  const filtered = notes.filter((n) => {
    const q = search.toLowerCase();
    return (
      (n.title || "").toLowerCase().includes(q) ||
      (n.content || "").toLowerCase().includes(q)
    );
  });

  const openNote = (note) => {
    setSelectedNote(note);
    setSidebarOpen(false);
  };

  return (
    <div className={`app-shell${dark ? " dark" : ""}`}>
      <div
        className={`sidebar-overlay${sidebarOpen ? " visible" : ""}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`sidebar${sidebarOpen ? " open" : ""}`}>
        <div className="sidebar-header">
          <span className="sidebar-heading">● All Notes</span>
          <button
            className="sidebar-close"
            onClick={() => setSidebarOpen(false)}
          >
            ✕
          </button>
        </div>

        <div className="sidebar-list">
          {notes.length === 0 ? (
            <p className="sidebar-empty">no notes yet</p>
          ) : (
            notes.map((note) => (
              <div
                key={note.id}
                className="sidebar-item"
                onClick={() => openNote(note)}
              >
                <p className="sidebar-item-title">
                  {note.title || "Untitled"}
                </p>
                <p className="sidebar-item-preview">{note.content}</p>
              </div>
            ))
          )}
        </div>

        <div className="sidebar-count">
          {notes.length} note{notes.length !== 1 ? "s" : ""}
        </div>
      </aside>

      <div className="app-inner">
        <div className="topbar">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(true)}
            title="Open notes list"
          >
            <span />
            <span />
            <span />
          </button>

          <span className="topbar-label">DevOps Workspace</span>

          <div className="topbar-right">
            <label
              className="theme-toggle"
              title={dark ? "Switch to light mode" : "Switch to dark mode"}
            >
              <span className="theme-toggle-icon">{dark ? "🌙" : "☀️"}</span>
              <div className="toggle-track" onClick={() => setDark(!dark)}>
                <div className="toggle-knob" />
              </div>
            </label>
          </div>
        </div>

        <header className="header">
          <p className="header-eyebrow">● Docker Notes</p>
          <h1 className="header-title">
            Capture. <span>Ship.</span>
          </h1>
          <p className="header-sub">// thoughts that keep the pipeline moving</p>
        </header>

        {selectedNote ? (
          <div className="compose-box">
            <button className="add-btn" onClick={() => setSelectedNote(null)}>
              ← Back to notes
            </button>

            <div style={{ marginTop: "24px" }}>
              <p className="note-index">#{selectedNote.id}</p>

              <h2 className="note-title" style={{ fontSize: "28px" }}>
                {selectedNote.title || "Untitled"}
              </h2>

              <p className="note-content" style={{ marginTop: "14px" }}>
                {selectedNote.content}
              </p>

              {selectedNote.created_at && (
                <p className="note-time">
                  saved at {formatTime(selectedNote.created_at)}
                </p>
              )}

              <button
                className="delete-btn"
                style={{ marginTop: "20px" }}
                onClick={() => deleteNote(selectedNote.id)}
                disabled={deletingId === selectedNote.id}
              >
                {deletingId === selectedNote.id ? "Deleting..." : "Delete note"}
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="compose-box">
              <input
                className="compose-title-input"
                type="text"
                placeholder="Note title..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />

              <textarea
                className="compose-textarea"
                placeholder="What's on your mind? // start typing..."
                value={content}
                rows={3}
                onChange={(e) => setContent(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                    addNote();
                  }
                }}
              />

              <div className="compose-footer">
                <span className="char-count">
                  {content.length} chars · Ctrl+Enter to save
                </span>

                <button
                  className="add-btn"
                  onClick={addNote}
                  disabled={adding || !content.trim()}
                >
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 14 14"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                  >
                    <line x1="7" y1="1" x2="7" y2="13" />
                    <line x1="1" y1="7" x2="13" y2="7" />
                  </svg>
                  {adding ? "Saving…" : "Add note"}
                </button>
              </div>
            </div>

            <div className="search-row">
              <input
                className="search-input"
                placeholder="Search by title or content..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <span className="notes-meta">
                {filtered.length} / {notes.length}
              </span>
            </div>

            {loading ? (
              <div className="loading-dots">
                <div className="dot" />
                <div className="dot" />
                <div className="dot" />
              </div>
            ) : filtered.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">◌</div>
                <p className="empty-label">
                  {search ? "no matches found" : "no notes yet — add one above"}
                </p>
              </div>
            ) : (
              <div className="notes-list">
                {filtered.map((note, i) => (
                  <div
                    className="note-card"
                    key={note.id}
                    id={`note-${note.id}`}
                    onClick={() => openNote(note)}
                  >
                    <span className="note-index">
                      {String(i + 1).padStart(2, "0")}
                    </span>

                    <div className="note-body">
                      <p className="note-title">{note.title || "Untitled"}</p>
                      <p className="note-content">{note.content}</p>

                      {note.created_at && (
                        <p className="note-time">
                          saved at {formatTime(note.created_at)}
                        </p>
                      )}
                    </div>

                    <button
                      className="delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNote(note.id);
                      }}
                      disabled={deletingId === note.id}
                      title="Delete note"
                    >
                      {deletingId === note.id ? "…" : "✕"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
