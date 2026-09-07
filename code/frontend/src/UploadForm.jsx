import { useState, useRef } from "react";
import { api } from "./api";

export default function UploadForm({ token }) {
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [file, setFile] = useState(null);
  const [coAuthorQuery, setCoAuthorQuery] = useState("");
  const [coAuthorResults, setCoAuthorResults] = useState([]);
  const [coAuthors, setCoAuthors] = useState([]); // [{id, full_name, email}]
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const searchDebounce = useRef(null);

  const handleCoAuthorSearch = (e) => {
    const q = e.target.value;
    setCoAuthorQuery(q);
    clearTimeout(searchDebounce.current);
    if (!q.trim()) {
      setCoAuthorResults([]);
      return;
    }
    searchDebounce.current = setTimeout(async () => {
      try {
        const users = await api.searchUsers(q, token);
        setCoAuthorResults(users.filter((u) => !coAuthors.some((c) => c.id === u.id)));
      } catch {
        setCoAuthorResults([]);
      }
    }, 250);
  };

  const addCoAuthor = (user) => {
    setCoAuthors([...coAuthors, user]);
    setCoAuthorResults([]);
    setCoAuthorQuery("");
  };

  const removeCoAuthor = (id) => setCoAuthors(coAuthors.filter((c) => c.id !== id));

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Client-side submit lock: an accidental double-click on the submit
    // button (or a slow network causing a re-click) can't fire a second
    // request while one is already in flight.
    if (isSubmitting) return;
    if (!file) {
      setError("Please choose a PDF file.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const paper = await api.uploadPaper(
        { title, abstract, file, coAuthorIds: coAuthors.map((c) => c.id) },
        token
      );
      setResult(paper);
      setTitle("");
      setAbstract("");
      setFile(null);
      setCoAuthors([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="upload-page">
      <h2>Upload a paper</h2>
      <form onSubmit={handleSubmit} className="form">
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Abstract
          <textarea
            value={abstract}
            onChange={(e) => setAbstract(e.target.value)}
            rows={4}
            required
          />
        </label>
        <label>
          PDF file
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </label>

        <label>
          Co-authors
          <input
            placeholder="Search by name or email..."
            value={coAuthorQuery}
            onChange={handleCoAuthorSearch}
          />
        </label>
        {coAuthorResults.length > 0 && (
          <ul className="typeahead">
            {coAuthorResults.map((u) => (
              <li key={u.id}>
                <button type="button" onClick={() => addCoAuthor(u)}>
                  {u.full_name} ({u.email})
                </button>
              </li>
            ))}
          </ul>
        )}
        {coAuthors.length > 0 && (
          <ul className="chip-list">
            {coAuthors.map((c) => (
              <li key={c.id} className="chip">
                {c.full_name}
                <button type="button" onClick={() => removeCoAuthor(c.id)} aria-label="Remove">
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}

        {error && <p className="error">{error}</p>}
        {result && (
          <p className="success">
            Uploaded "{result.title}" — status: {result.status}
          </p>
        )}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Uploading..." : "Upload paper"}
        </button>
      </form>
    </div>
  );
}
