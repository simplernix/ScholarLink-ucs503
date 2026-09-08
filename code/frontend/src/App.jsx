import { useState } from "react";
import { api } from "./api";
import UploadForm from "./UploadForm.jsx";
import "./App.css";

/* =========================================================
   MOCK DATA
   Used only while building the frontend.
   These will later be replaced with API data.
========================================================= */

const mockPapers = [
  {
    id: 1,
    title: "Machine Learning Approaches for Predictive Healthcare",
    abstract:
      "An exploration of machine learning techniques for improving predictive analysis and decision support in modern healthcare systems.",
    authors: ["Aarav Sharma", "Priya Mehta"],
    date: "Sep 04, 2026",
    views: 248,
    status: "Published",
  },
  {
    id: 2,
    title: "A Comparative Study of Cloud Computing Architectures",
    abstract:
      "A comparative analysis of modern cloud architectures with emphasis on scalability, reliability, and distributed application performance.",
    authors: ["Rahul Verma", "Neha Kapoor"],
    date: "Aug 28, 2026",
    views: 184,
    status: "Published",
  },
  {
    id: 3,
    title: "Artificial Intelligence in Academic Research",
    abstract:
      "Investigating the evolving role of artificial intelligence tools in academic research, collaboration, and knowledge discovery.",
    authors: ["Simran Kaur"],
    date: "Aug 16, 2026",
    views: 126,
    status: "Published",
  },
];

const mockResearchers = [
  {
    name: "Aarav Sharma",
    role: "Professor",
    field: "Artificial Intelligence",
    papers: 24,
    initials: "AS",
  },
  {
    name: "Priya Mehta",
    role: "Research Scholar",
    field: "Data Science",
    papers: 18,
    initials: "PM",
  },
  {
    name: "Rahul Verma",
    role: "Professor",
    field: "Cloud Computing",
    papers: 31,
    initials: "RV",
  },
  {
    name: "Neha Kapoor",
    role: "Research Scholar",
    field: "Cybersecurity",
    papers: 15,
    initials: "NK",
  },
];

/* =========================================================
   SIDEBAR
========================================================= */

function Sidebar({ activePage, setActivePage, onLogout }) {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: "⌂" },
    { id: "papers", label: "My Papers", icon: "▤" },
    { id: "researchers", label: "Researchers", icon: "♧" },
    { id: "upload", label: "Upload Paper", icon: "↑" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">S</div>

        <div>
          <div className="brand-name">ScholarLink</div>
          <div className="brand-caption">Research Network</div>
        </div>
      </div>

      <div className="sidebar-section-title">WORKSPACE</div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`sidebar-item ${
              activePage === item.id ? "active" : ""
            }`}
            onClick={() => setActivePage(item.id)}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-spacer" />

      <div className="sidebar-section-title">ACCOUNT</div>

      <button
        className={`sidebar-item ${
          activePage === "profile" ? "active" : ""
        }`}
        onClick={() => setActivePage("profile")}
      >
        <span className="sidebar-icon">◯</span>
        <span>Profile</span>
      </button>

      <button className="sidebar-item">
        <span className="sidebar-icon">⚙</span>
        <span>Settings</span>
      </button>

      <button className="sidebar-item logout-item" onClick={onLogout}>
        <span className="sidebar-icon">↪</span>
        <span>Sign out</span>
      </button>

      <div className="sidebar-footer">
        <div className="sidebar-footer-mark">SL</div>

        <div>
          <strong>ScholarLink</strong>
          <span>Academic collaboration</span>
        </div>
      </div>
    </aside>
  );
}

/* =========================================================
   TOPBAR
========================================================= */

function Topbar({ user, activePage }) {
  const displayName = user?.full_name || "Researcher";

  const pageTitles = {
    dashboard: "Dashboard",
    papers: "My Papers",
    researchers: "Researchers",
    upload: "Upload Paper",
    profile: "Profile",
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="mobile-brand">
          <div className="brand-mark small">S</div>
          <span>ScholarLink</span>
        </div>

        <div className="breadcrumb">
          <span>Workspace</span>
          <span className="breadcrumb-separator">/</span>
          <strong>{pageTitles[activePage] || "Dashboard"}</strong>
        </div>
      </div>

      <div className="topbar-right">
        <button className="icon-button" aria-label="Search">
          ⌕
        </button>

        <button
          className="icon-button notification-button"
          aria-label="Notifications"
        >
          ♢
          <span className="notification-dot" />
        </button>

        <div className="topbar-divider" />

        <div className="user-menu">
          <div className="avatar">
            {displayName.charAt(0).toUpperCase()}
          </div>

          <div className="user-menu-info">
            <strong>{displayName}</strong>
            <span>{user?.role || "Researcher"}</span>
          </div>

          <span className="user-chevron">⌄</span>
        </div>
      </div>
    </header>
  );
}

/* =========================================================
   STAT CARD
========================================================= */

function StatCard({ label, value, change, description, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <div className="stat-icon">{icon}</div>

        {change && <span className="stat-change">↗ {change}</span>}
      </div>

      <div className="stat-value">{value}</div>

      <div className="stat-label">{label}</div>

      {description && (
        <div className="stat-description">{description}</div>
      )}
    </div>
  );
}

/* =========================================================
   PAPER CARD
========================================================= */

function PaperCard({ paper }) {
  return (
    <article className="paper-card">
      <div className="paper-card-main">
        <div className="paper-type">RESEARCH PAPER</div>

        <h3>{paper.title}</h3>

        <p>{paper.abstract}</p>

        <div className="paper-meta">
          <div className="paper-authors">
            <div className="author-stack">
              {paper.authors.slice(0, 3).map((author, index) => (
                <div
                  className="mini-avatar"
                  key={`${author}-${index}`}
                  title={author}
                >
                  {author.charAt(0)}
                </div>
              ))}
            </div>

            <span>
              {paper.authors.length > 1
                ? `${paper.authors[0]} + ${
                    paper.authors.length - 1
                  } others`
                : paper.authors[0]}
            </span>
          </div>

          <span className="paper-date">{paper.date}</span>
        </div>
      </div>

      <div className="paper-card-side">
        <span className="paper-status">{paper.status}</span>

        <div className="paper-views">
          <span>◉</span>
          {paper.views} views
        </div>

        <button className="paper-open">
          View paper <span>→</span>
        </button>
      </div>
    </article>
  );
}

/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard({ user, setActivePage }) {
  const displayName = user?.full_name || "Researcher";

  return (
    <div className="page-content">
      <section className="dashboard-hero">
        <div className="hero-copy">
          <span className="eyebrow">RESEARCH WORKSPACE</span>

          <h1>
            Welcome back,
            <br />
            <span>{displayName}</span>
          </h1>

          <p>
            Share your research, connect with collaborators, and
            build meaningful academic connections.
          </p>

          <div className="hero-actions">
            <button
              className="primary-btn dashboard-action"
              onClick={() => setActivePage("upload")}
            >
              <span>Upload research</span>
              <span className="arrow">→</span>
            </button>

            <button
              className="secondary-btn"
              onClick={() => setActivePage("researchers")}
            >
              Discover researchers
            </button>
          </div>
        </div>

        <div className="hero-badge">
          <span className="status-dot" />

          <div>
            <strong>Account active</strong>
            <small>{user?.role || "Researcher"} account</small>
          </div>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          label="My Papers"
          value="12"
          change="+3 this month"
          description="Research library"
          icon="▣"
        />

        <StatCard
          label="Collaborators"
          value="08"
          change="+2 this month"
          description="Research network"
          icon="◉"
        />

        <StatCard
          label="Total Views"
          value="1,248"
          change="+18.4%"
          description="Across your publications"
          icon="◌"
        />

        <StatCard
          label="Research Impact"
          value="86"
          change="+12%"
          description="Engagement score"
          icon="✦"
        />
      </section>

      <section className="dashboard-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">YOUR LIBRARY</span>
            <h2>Recent research</h2>
          </div>

          <button
            className="text-button"
            onClick={() => setActivePage("papers")}
          >
            View all <span>→</span>
          </button>
        </div>

        <div className="paper-list">
          {mockPapers.slice(0, 2).map((paper) => (
            <PaperCard paper={paper} key={paper.id} />
          ))}
        </div>
      </section>

      <section className="dashboard-bottom-grid">
        <div className="insight-card">
          <div className="insight-icon">✦</div>

          <div>
            <span className="eyebrow">SCHOLARLINK INSIGHT</span>
            <h3>Research is better together.</h3>
            <p>
              Connect with researchers who share your interests and
              discover new opportunities for collaboration.
            </p>
          </div>

          <button
            className="text-button"
            onClick={() => setActivePage("researchers")}
          >
            Explore network →
          </button>
        </div>

        <div className="activity-card">
          <div className="section-heading compact-heading">
            <div>
              <span className="eyebrow">ACTIVITY</span>
              <h2>Recent updates</h2>
            </div>
          </div>

          <div className="activity-item">
            <div className="activity-dot" />
            <div>
              <strong>Research profile updated</strong>
              <span>Today · 10:42 AM</span>
            </div>
          </div>

          <div className="activity-item">
            <div className="activity-dot" />
            <div>
              <strong>New collaboration opportunity</strong>
              <span>Yesterday · 4:18 PM</span>
            </div>
          </div>

          <div className="activity-item">
            <div className="activity-dot" />
            <div>
              <strong>Paper received 24 new views</strong>
              <span>2 days ago</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

/* =========================================================
   PAPERS PAGE
========================================================= */

function PapersPage({ setActivePage }) {
  return (
    <div className="page-content">
      <section className="page-header">
        <div>
          <span className="eyebrow">RESEARCH LIBRARY</span>
          <h1>My Papers</h1>
          <p>
            Manage your research publications and track their
            engagement.
          </p>
        </div>

        <button
          className="primary-btn dashboard-action"
          onClick={() => setActivePage("upload")}
        >
          Upload paper <span className="arrow">→</span>
        </button>
      </section>

      <div className="library-toolbar">
        <div className="search-box">
          <span>⌕</span>
          <input placeholder="Search your papers..." />
        </div>

        <button className="filter-button">All papers⌄</button>
      </div>

      <div className="paper-list full-list">
        {mockPapers.map((paper) => (
          <PaperCard paper={paper} key={paper.id} />
        ))}
      </div>
    </div>
  );
}

/* =========================================================
   RESEARCHERS PAGE
========================================================= */

function ResearchersPage() {
  return (
    <div className="page-content">
      <section className="page-header">
        <div>
          <span className="eyebrow">RESEARCH NETWORK</span>
          <h1>Discover researchers</h1>
          <p>
            Find researchers and potential collaborators across
            different academic fields.
          </p>
        </div>
      </section>

      <div className="researcher-toolbar">
        <div className="search-box">
          <span>⌕</span>
          <input placeholder="Search researchers or research areas..." />
        </div>

        <button className="filter-button">All fields⌄</button>
      </div>

      <div className="researcher-grid">
        {mockResearchers.map((researcher) => (
          <article className="researcher-card" key={researcher.name}>
            <div className="researcher-card-top">
              <div className="researcher-avatar">
                {researcher.initials}
              </div>

              <button className="more-button">•••</button>
            </div>

            <h3>{researcher.name}</h3>

            <span className="researcher-role">
              {researcher.role}
            </span>

            <div className="research-field">
              <span>◈</span>
              {researcher.field}
            </div>

            <div className="researcher-footer">
              <div>
                <strong>{researcher.papers}</strong>
                <span>Publications</span>
              </div>

              <button className="connect-button">
                View profile →
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

/* =========================================================
   UPLOAD PAGE
========================================================= */

function UploadPage({ token }) {
  return (
    <div className="page-content">
      <section className="page-header upload-page-header">
        <div>
          <span className="eyebrow">PUBLISH</span>
          <h1>Upload research</h1>
          <p>
            Share your latest work with the ScholarLink research
            community.
          </p>
        </div>

        <div className="upload-step">
          <span>01</span>
          <div>
            <strong>Research submission</strong>
            <small>Secure publication workflow</small>
          </div>
        </div>
      </section>

      <section className="upload-layout">
        <div className="upload-main-card">
          <UploadForm token={token} />
        </div>

        <aside className="upload-info-card">
          <div className="side-card-icon">✦</div>

          <span className="eyebrow">SUBMISSION GUIDE</span>

          <h3>Prepare your research.</h3>

          <p>
            Add a clear title, concise abstract, PDF document, and
            collaborators to make your research easy to discover.
          </p>

          <div className="guide-list">
            <div>
              <span>01</span>
              <p>Use a descriptive research title</p>
            </div>

            <div>
              <span>02</span>
              <p>Write a concise abstract</p>
            </div>

            <div>
              <span>03</span>
              <p>Upload your final PDF document</p>
            </div>

            <div>
              <span>04</span>
              <p>Add your co-authors when applicable</p>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}

/* =========================================================
   PROFILE PAGE
========================================================= */

function ProfilePage({ user }) {
  const displayName = user?.full_name || "Researcher";

  return (
    <div className="page-content">
      <section className="page-header">
        <div>
          <span className="eyebrow">ACCOUNT</span>
          <h1>Your profile</h1>
          <p>
            Manage your ScholarLink research identity and account
            information.
          </p>
        </div>
      </section>

      <section className="profile-layout">
        <div className="profile-card profile-main-card">
          <div className="profile-cover" />

          <div className="profile-body">
            <div className="large-avatar">
              {displayName.charAt(0).toUpperCase()}
            </div>

            <h2>{displayName}</h2>

            <span className="profile-role">
              {user?.role || "Researcher"}
            </span>

            <div className="profile-divider" />

            <div className="profile-detail">
              <span>Email address</span>
              <strong>{user?.email || "Not available"}</strong>
            </div>

            <div className="profile-detail">
              <span>Account type</span>
              <strong>{user?.role || "Researcher"}</strong>
            </div>

            <div className="profile-detail">
              <span>Research papers</span>
              <strong>12 publications</strong>
            </div>
          </div>
        </div>

        <div className="profile-card profile-stats-card">
          <span className="eyebrow">RESEARCH OVERVIEW</span>

          <h3>Your research presence</h3>

          <div className="profile-stat">
            <strong>12</strong>
            <span>Published papers</span>
          </div>

          <div className="profile-stat">
            <strong>08</strong>
            <span>Collaborators</span>
          </div>

          <div className="profile-stat">
            <strong>1.2K</strong>
            <span>Total research views</span>
          </div>

          <button className="secondary-btn profile-edit-button">
            Edit profile
          </button>
        </div>
      </section>
    </div>
  );
}

/* =========================================================
   MAIN APPLICATION
========================================================= */

export default function App() {
  const [mode, setMode] = useState("login");

  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "student",
  });

  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [activePage, setActivePage] = useState("dashboard");

  const update = (field) => (e) => {
    setForm({
      ...form,
      [field]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await api.register(form);

        setMode("login");
        setError(null);
      } else {
        const data = await api.login({
          email: form.email,
          password: form.password,
        });

        setToken(data.access_token);
        setUser(data.user);
        setActivePage("dashboard");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setActivePage("dashboard");

    setForm({
      email: "",
      password: "",
      full_name: "",
      role: "student",
    });
  };

  /* =======================================================
     AUTHENTICATION SCREEN
  ======================================================= */

  if (!user) {
    return (
      <div className="auth-page">
        <div className="auth-visual">
          <div className="visual-content">
            <div className="brand light-brand">
              <div className="brand-mark">S</div>

              <div>
                <span className="brand-name">ScholarLink</span>
                <span className="brand-subtitle">
                  Research Network
                </span>
              </div>
            </div>

            <div className="visual-main">
              <span className="eyebrow light">
                THE RESEARCH NETWORK
              </span>

              <h1>
                Discover ideas.
                <br />
                <span>Connect minds.</span>
                <br />
                Create impact.
              </h1>

              <p>
                A collaborative platform designed to help students
                and professors share research, find collaborators,
                and build the future of knowledge together.
              </p>
            </div>

            <div className="visual-footer">
              <div>
                <strong>01</strong>
                <span>Share research</span>
              </div>

              <div>
                <strong>02</strong>
                <span>Find collaborators</span>
              </div>

              <div>
                <strong>03</strong>
                <span>Grow together</span>
              </div>
            </div>
          </div>

          <div className="orb orb-one" />
          <div className="orb orb-two" />
          <div className="grid-pattern" />
        </div>

        <div className="auth-panel">
          <div className="auth-container">
            <div className="mobile-brand">
              <div className="brand-mark">S</div>
              <span>ScholarLink</span>
            </div>

            <div className="auth-heading">
              <span className="eyebrow">
                {mode === "login"
                  ? "WELCOME BACK"
                  : "JOIN SCHOLARLINK"}
              </span>

              <h2>
                {mode === "login"
                  ? "Sign in to your workspace."
                  : "Start your research journey."}
              </h2>

              <p>
                {mode === "login"
                  ? "Enter your credentials to continue."
                  : "Create your account and join the research community."}
              </p>
            </div>

            <div className="auth-tabs">
              <button
                className={
                  mode === "login"
                    ? "auth-tab active"
                    : "auth-tab"
                }
                onClick={() => {
                  setMode("login");
                  setError(null);
                }}
              >
                Sign in
              </button>

              <button
                className={
                  mode === "register"
                    ? "auth-tab active"
                    : "auth-tab"
                }
                onClick={() => {
                  setMode("register");
                  setError(null);
                }}
              >
                Create account
              </button>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              {mode === "register" && (
                <>
                  <div className="field">
                    <label htmlFor="full_name">Full name</label>

                    <input
                      id="full_name"
                      type="text"
                      placeholder="Your full name"
                      value={form.full_name}
                      onChange={update("full_name")}
                      required
                    />
                  </div>

                  <div className="field">
                    <label htmlFor="role">I am a</label>

                    <select
                      id="role"
                      value={form.role}
                      onChange={update("role")}
                    >
                      <option value="student">Student</option>
                      <option value="professor">Professor</option>
                    </select>
                  </div>
                </>
              )}

              <div className="field">
                <label htmlFor="email">Email address</label>

                <input
                  id="email"
                  type="email"
                  placeholder="you@university.edu"
                  value={form.email}
                  onChange={update("email")}
                  required
                />
              </div>

              <div className="field">
                <div className="field-label-row">
                  <label htmlFor="password">Password</label>

                  {mode === "login" && (
                    <span className="helper-text">
                      Secure access
                    </span>
                  )}
                </div>

                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={update("password")}
                  required
                />
              </div>

              {error && (
                <div className="message error">
                  <span>!</span>
                  {error}
                </div>
              )}

              <button
                className="primary-btn"
                type="submit"
                disabled={isSubmitting}
              >
                <span>
                  {isSubmitting
                    ? "Please wait..."
                    : mode === "login"
                    ? "Sign in"
                    : "Create account"}
                </span>

                {!isSubmitting && (
                  <span className="arrow">→</span>
                )}
              </button>
            </form>

            <div className="auth-note">
              <span className="lock-icon">◇</span>
              Your research workspace is protected with secure
              authentication.
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* =======================================================
     LOGGED-IN APPLICATION
  ======================================================= */

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        onLogout={logout}
      />

      <div className="app-main">
        <Topbar user={user} activePage={activePage} />

        <main>
          {activePage === "dashboard" && (
            <Dashboard
              user={user}
              setActivePage={setActivePage}
            />
          )}

          {activePage === "papers" && (
            <PapersPage setActivePage={setActivePage} />
          )}

          {activePage === "researchers" && (
            <ResearchersPage />
          )}

          {activePage === "upload" && (
            <UploadPage token={token} />
          )}

          {activePage === "profile" && (
            <ProfilePage user={user} />
          )}
        </main>
      </div>
    </div>
  );
}