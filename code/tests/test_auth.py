"""
TDD: these tests define the required behavior of /auth/register and
/auth/login before/alongside the implementation in app/services/auth_service.py
and app/routes/auth_routes.py.
"""
from app.core.enums import UserRole


def test_register_creates_user_and_hashes_password(client, db_session):
    resp = client.post(
        "/auth/register",
        json={
            "email": "new.student@university.edu",
            "password": "supersecret1",
            "full_name": "Nova Student",
            "role": "student",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "new.student@university.edu"
    assert body["role"] == "student"
    assert "password" not in body
    assert "hashed_password" not in body

    from app.models.user import User

    stored = db_session.query(User).filter(User.email == "new.student@university.edu").one()
    assert stored.hashed_password != "supersecret1"


def test_register_duplicate_email_returns_clean_conflict_not_crash(client):
    payload = {
        "email": "dupe@university.edu",
        "password": "supersecret1",
        "full_name": "First Person",
        "role": "student",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json={**payload, "full_name": "Second Person"})
    assert second.status_code == 409
    assert "already registered" in second.json()["detail"].lower()


def test_login_with_correct_credentials_returns_token(client, make_user):
    make_user(email="prof@university.edu", password="mypassword1", role=UserRole.PROFESSOR)

    resp = client.post(
        "/auth/login", json={"email": "prof@university.edu", "password": "mypassword1"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["user"]["email"] == "prof@university.edu"


def test_login_with_wrong_password_is_rejected(client, make_user):
    make_user(email="student@university.edu", password="correct-password")

    resp = client.post(
        "/auth/login", json={"email": "student@university.edu", "password": "wrong-password"}
    )
    assert resp.status_code == 401
    assert "access_token" not in resp.json()


def test_login_unknown_email_is_rejected_same_as_wrong_password(client):
    resp = client.post("/auth/login", json={"email": "ghost@university.edu", "password": "x"})
    assert resp.status_code == 401


def test_login_deactivated_account_is_rejected(client, make_user):
    make_user(email="deactivated@university.edu", password="password123", is_active=False)

    resp = client.post(
        "/auth/login", json={"email": "deactivated@university.edu", "password": "password123"}
    )
    assert resp.status_code == 403


def test_protected_route_rejects_invalid_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_protected_route_rejects_missing_token(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_protected_route_accepts_valid_token(client, make_user):
    make_user(email="me@university.edu", password="password123")
    login = client.post(
        "/auth/login", json={"email": "me@university.edu", "password": "password123"}
    )
    token = login.json()["access_token"]

    resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@university.edu"
