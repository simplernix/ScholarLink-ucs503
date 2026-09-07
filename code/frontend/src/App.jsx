import { useState } from "react";
import { api } from "./api";
import UploadForm from "./UploadForm.jsx";
import "./App.css";

export default function App() {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({ email: "", password: "", full_name: "", role: "student" });
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [error, setError] = useState(null);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "register") {
        await api.register(form);
        setMode("login");
        return;
      }
      const data = await api.login({ email: form.email, password: form.password });
      setToken(data.access_token);
      setUser(data.user);
    } catch (err) {
      setError(err.message);
    }
  };

  if (user) {
    return (
      <div className="page wide">
        <h1>Welcome, {user.full_name}</h1>
        <p>Role: {user.role}</p>
        <UploadForm token={token} />
        <p className="muted">
          Search, discovery, and collaboration requests land in later phases.
        </p>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>ScholarLink</h1>
      <div className="tabs">
        <button onClick={() => setMode("login")} disabled={mode === "login"}>
          Log in
        </button>
        <button onClick={() => setMode("register")} disabled={mode === "register"}>
          Register
        </button>
      </div>
      <form onSubmit={handleSubmit} className="form">
        {mode === "register" && (
          <>
            <label>
              Full name
              <input value={form.full_name} onChange={update("full_name")} required />
            </label>
            <label>
              Role
              <select value={form.role} onChange={update("role")}>
                <option value="student">Student</option>
                <option value="professor">Professor</option>
              </select>
            </label>
          </>
        )}
        <label>
          Email
          <input type="email" value={form.email} onChange={update("email")} required />
        </label>
        <label>
          Password
          <input type="password" value={form.password} onChange={update("password")} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">{mode === "register" ? "Create account" : "Log in"}</button>
      </form>
    </div>
  );
}
