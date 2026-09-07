# ScholarLink

A platform where students and professors upload research papers, get
AI-generated topic tags and future-scope summaries, and discover
collaborators.

This repo is being built phase-by-phase. **Phase 1 (Foundation & Auth)** is
complete. See `PHASE_LOG.md` for a running log of what's been built in each
phase and how to verify it.

## Tech stack

- **Backend:** Python / FastAPI, Route → Service → Repository layering
- **Database:** PostgreSQL + SQLAlchemy ORM + Alembic migrations
- **Frontend:** React
- **Auth:** JWT, role-based access control (Student / Professor / Admin)
- **Testing:** pytest (TDD)
- **CI/CD:** GitHub Actions
- **Containerization:** Docker / docker-compose

## Project layout

```
app/
  core/          # config, db session, security (hashing/JWT), enums
  models/        # SQLAlchemy ORM models (all 8 core entities)
  repositories/  # DB access only — no business logic
  services/      # business logic — no DB access, no HTTP concerns
  routes/        # FastAPI routers — no business logic, no DB access
alembic/         # migrations
tests/           # pytest suite (unit + integration)
frontend/        # React app (skeleton in Phase 1, built out in later phases)
```

## Local setup

1. Copy `.env.example` to `.env` and adjust if needed.
2. Start Postgres: `docker-compose up -d db`
3. Install backend deps: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Run the API: `uvicorn app.main:app --reload`
6. Run tests: `pytest`

Interactive API docs: http://localhost:8000/docs
