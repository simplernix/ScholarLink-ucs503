# ScholarLink — Phase Log

## Phase 1 — Foundation & Auth ✅ complete, tests green

### What was built

**1.1 Repo & CI/CD skeleton**
- Route → Service → Repository folder layout: `app/routes`, `app/services`,
  `app/repositories`, `app/models`, `app/core`, `app/schemas`.
- `/frontend` — minimal Vite + React skeleton (login/register screens
  wired to the real `/auth` endpoints; proxies `/auth`, `/admin`, `/users`,
  `/papers` to `localhost:8000` in dev).
- `docker-compose.yml` — Postgres + API services. Postgres uses a **named
  volume** (`scholarlink_db_data`) so repeat `docker-compose up` never
  wipes data. API container runs `alembic upgrade head` before serving, so
  bringing the stack up is itself idempotent.
- `.env.example` with `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`,
  `ACCESS_TOKEN_EXPIRE_MINUTES`, `UPLOAD_DIR`. No real secrets committed.
- `.github/workflows/ci.yml` — `test` (pytest against a real Postgres
  service container) → `build` (Docker image, buildx/gha cache) → `deploy`
  (stub, always safe to re-run, only fires on `main`).

**1.2 Database schema & ORM layer**
- All 8 core entities modeled: `User`, `Paper`, `PaperAuthor`, `Topic`,
  `PaperTopic`, `PaperInsight`, `CollaborationRequest`, `Notification`
  (`app/models/`). Later-phase fields (e.g. `Paper.status`,
  `PaperInsight`, `bio`/`department` on `User`) are modeled now per the
  global schema-up-front instruction, even though only `User` has live
  endpoints in Phase 1.
- `User` includes `email`, `hashed_password`, `role` (enum), `is_active`,
  `institutional_email_domain`, `is_institution_verified`.
- Status/role/event fields use native enums (`app/core/enums.py`), not
  free-text strings.
- One hand-written initial Alembic migration
  (`alembic/versions/4fd2798321d2_initial_schema.py`) creating all 8
  tables with FKs and unique constraints, with a full **reversible
  `downgrade()`** — including dropping the Postgres enum types it created,
  so `downgrade` → `upgrade` again doesn't fail with "type already exists".
- `alembic/env.py` reads `DATABASE_URL` from `app.core.config.settings` and
  imports `app.models` so autogeneration (for future migrations) sees the
  full metadata.

**1.3 JWT authentication**
- `POST /auth/register`, `POST /auth/login` (Route → Service →
  Repository: `auth_routes.py` → `AuthService` → `UserRepository`).
- Passwords hashed with bcrypt via `passlib`.
- JWT issue/verify in `app/core/security.py`; `get_current_user` FastAPI
  dependency in `app/core/deps.py`.
- Duplicate registration returns a clean `409 Conflict`
  (`EmailAlreadyRegisteredError`) — never a raw DB `IntegrityError`.
- TDD tests in `tests/test_auth.py` (written alongside the service):
  successful register, duplicate-email conflict, valid login, wrong
  password, unknown email, deactivated account, and protected-route token
  checks (missing/invalid/valid).

**1.4 RBAC & admin user management**
- `require_role(*roles)` dependency built on `get_current_user`
  (`app/core/deps.py`).
- Admin-only routes (`app/routes/admin_routes.py`, all gated by
  `require_role(UserRole.ADMIN)`):
  - `POST /admin/users/{id}/verify-institution`
  - `POST /admin/users/{id}/deactivate`
- Both actions are **idempotent** at the service layer (`UserService`):
  they only write when the field would actually change, so calling them
  twice is a no-op the second time, not an error or duplicate mutation.
- TDD tests in `tests/test_rbac.py`: admin allowed, student denied,
  professor denied (not just "any non-admin"), no-token denied,
  deactivate-twice-is-idempotent, verify-twice-is-idempotent, a
  deactivated admin's own token stops working immediately, and
  admin-action-on-unknown-user returns `404`.

### Test results

```
17 passed in ~9s
```
Ran twice back-to-back with no manual cleanup between runs — same result
both times.

### How to verify locally

```bash
cd scholarlink
cp .env.example .env
pip install -r requirements.txt
pytest                      # 17 passed
docker-compose up -d db     # start Postgres only
alembic upgrade head        # apply migration to real Postgres
uvicorn app.main:app --reload
# in another shell:
curl -X POST localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"email":"a@uni.edu","password":"password123","full_name":"A","role":"student"}'
curl -X POST localhost:8000/auth/login -H 'content-type: application/json' \
  -d '{"email":"a@uni.edu","password":"password123"}'
```
Full stack via Docker: `docker-compose up --build` (runs migrations then
serves the API on `:8000`).

Frontend (optional, for the login/register skeleton):
```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
```

### Assumptions made (flag if you want these changed)

1. **Tests run against in-memory SQLite, not Postgres.** All model types
   used (Postgres `UUID`, `Enum`) compile fine under SQLite, so this is
   safe for Phase 1's behavior and keeps `pytest` fast with zero external
   services. CI's `test` job additionally runs the same suite against a
   **real Postgres** service container and applies the actual Alembic
   migration first, so the Postgres path is exercised too. If you'd
   rather all local test runs hit Postgres directly, say so and I'll swap
   the fixture.
2. **JWT expiry default: 60 minutes**, configurable via
   `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`.
3. **Institutional email domain** is auto-derived from the part after `@`
   at registration time and stored on `User.institutional_email_domain`;
   admin "verification" is a separate boolean (`is_institution_verified`)
   rather than re-deriving the domain, so verification is a pure status
   flip.
4. **Frontend uses Vite**, not Create React App (CRA is unmaintained) —
   still plain React, just a lighter/faster toolchain. `npm install` was
   not run in the sandbox (no need to fetch ~995 packages to prove out a
   Phase 1 skeleton), so please run it once locally before `npm run dev`.
5. **CI `deploy` stage** is an explicit no-op stub gated to `main`, per
   the spec — it will be filled in during Phase 6.

### Next up

Phase 2 — Paper Upload Pipeline (upload UI + endpoint, UUID-keyed file
storage, PDF text extraction). Say the word and I'll continue.

---

## Phase 2 — Paper Upload Pipeline ✅ complete, tests green

### What was built

**2.1 Upload UI & endpoint**
- `frontend/src/UploadForm.jsx` — title, abstract, PDF file picker, and a
  debounced co-author search-and-tag widget (calls `GET /users/search`,
  lets you add/remove chips before submitting).
- **Client-side submit lock**: the submit button is `disabled` while a
  request is in flight (`isSubmitting` state), so a double-click can't
  fire a second HTTP request.
- `POST /papers` (multipart/form-data: `title`, `abstract`, `file`,
  optional comma-separated `co_author_ids`) via
  `paper_routes.py` → `PaperService` → `PaperRepository` /
  `UserRepository`. Requires authentication.
- **Server-side idempotency**: `PaperRepository.find_recent_by_uploader_and_title`
  looks for a paper this same uploader created with this exact title in
  the last 10 seconds (configurable); if found, the service returns that
  existing paper instead of creating a new one and instead of re-saving
  the uploaded file — so an accidental double-submit (e.g. a slow network
  causing a duplicate click before the button disables) still can't create
  two records.

**2.2 File storage & record creation**
- `app/core/storage.py::UploadStorage` — every upload is written under a
  fresh `uuid4()`-based filename (extension preserved, original filename
  discarded); a same-named re-upload can never collide or overwrite. Also
  raises rather than silently overwriting in the astronomically unlikely
  case of a UUID collision.
- `Paper` + `PaperAuthor` records created together; the uploader is always
  linked as author `#0`. Co-authors are linked **only if they already
  exist** as a `User` (`UserRepository.get_by_id` lookup) — an unknown id
  in the co-author list is silently skipped rather than failing the whole
  upload or creating a phantom user.
- `PaperAuthor` linking uses get-or-create (`PaperRepository.add_author_link`),
  so linking the same (paper, user) pair twice is a no-op, not a duplicate
  row or an `IntegrityError`.
- `Paper.status` lifecycle (`PROCESSING` → `PUBLISHED`) already modeled as
  a native enum in Phase 1; every paper is created as `PROCESSING` here.
  It doesn't move to `PUBLISHED` yet — that transition is Phase 3's job
  (after LLM extraction succeeds), per the phase ordering rule.

**2.3 PDF text extraction**
- `app/services/pdf_extraction.py::extract_pdf_text` using PyMuPDF
  (`fitz`), raising a clear `ValueError` for unreadable/non-PDF bytes.
- Wired up for now as a **manual trigger**, `POST /papers/{id}/extract-text`
  (Phase 3 will call this same service method automatically from the
  background job queue when a paper enters `Processing`).
- `PaperRepository.update_extracted_text` **overwrites** the
  `extracted_text` column on the existing `Paper` row — re-running
  extraction (e.g. after a simulated crash-and-retry) replaces the text
  rather than appending to it or creating a second row, since it's a
  column update, not an insert.

### New/changed dependencies
- `PyMuPDF==1.24.10` (imported as `fitz`) for PDF text extraction.
- `email-validator==2.2.0` — required by Pydantic's `EmailStr`; was
  missing from Phase 1's `requirements.txt` and has been added (also
  fixed a Phase-1 test-import bug this surfaced: `import app.models` in
  `conftest.py` was shadowing the `app` FastAPI instance name — fixed by
  importing it as `from app import models as _models`).

### Test results

```
30 passed  (17 from Phase 1 + 13 new Phase 2 tests)
```
Ran 3x back-to-back with no manual cleanup — same result every time.
New tests (`tests/test_paper_upload.py`) cover: paper created with
uploader as author, double-submit returns the same paper (both at the
HTTP-response level and by directly counting DB rows), different titles
from the same uploader create separate papers, UUID storage keys never
contain the original filename and both files exist on disk, linking an
existing co-author without creating a duplicate `User`, silently skipping
an unknown co-author id, upload requiring auth, extraction populating
`extracted_text`, re-extraction overwriting (not duplicating) the text
and row, extraction on an unknown paper returning `404`, and the
co-author search endpoint (found/not-found/requires-auth).

### How to verify locally

```bash
cd scholarlink
pip install -r requirements.txt      # picks up PyMuPDF + email-validator
pytest                                # 30 passed
uvicorn app.main:app --reload
```
Then, with a token from `/auth/login`:
```bash
curl -X POST localhost:8000/papers \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=My Paper" -F "abstract=An abstract" -F "file=@/path/to/some.pdf"

curl -X POST localhost:8000/papers/<paper_id>/extract-text \
  -H "Authorization: Bearer $TOKEN"

curl "localhost:8000/users/search?q=ada" -H "Authorization: Bearer $TOKEN"
```
Frontend: `cd frontend && npm install && npm run dev`, log in, and use the
upload form (co-author search works once you've registered a couple of
test users).

### Assumptions made (flag if you want these changed)

1. **Double-submit dedupe window: 10 seconds**, matched on
   `(uploaded_by_id, title)` exactly (case-sensitive). A genuine second
   upload with the exact same title more than 10 seconds later, or a
   different title, always creates a new paper. If you want fuzzy title
   matching or a different window, easy to adjust in
   `PaperService.DEFAULT_DEDUPE_WINDOW_SECONDS`.
2. **Co-author ids are sent as a comma-separated form field**
   (`co_author_ids=uuid1,uuid2`), not a JSON array, since the endpoint has
   to be `multipart/form-data` to carry the file. Malformed/unknown ids in
   that list are silently skipped rather than rejecting the whole upload.
3. **Text extraction is a manual `POST .../extract-text` trigger for now**,
   not automatic — Phase 3 (background job infra) is what's supposed to
   fire this automatically when a paper enters `Processing`, per the
   phase ordering rules. The extraction logic itself is already fully
   built and tested so Phase 3 just has to call it from a worker.
4. **`Paper.status` stays `PROCESSING`** after upload and after manual
   extraction in this phase — nothing moves it to `PUBLISHED` yet. That
   transition is explicitly Phase 3's responsibility ("move the paper to
   Published only after \[LLM extraction\] succeeds").
5. Reused the Phase 1 in-memory-SQLite test strategy; CI's `test` job
   still additionally runs everything against real Postgres.

### Next up

Phase 3 — LLM Topic & Future-Scope Extraction (background job
infrastructure, structured LLM prompt, topic-matching/dedup, moving the
paper to `Published`). Say the word and I'll continue.
