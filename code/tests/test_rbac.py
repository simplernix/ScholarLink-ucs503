"""
TDD: RBAC behavior for require_role() and the admin-only endpoints built
on top of it.
"""
from app.core.enums import UserRole


def _login(client, email, password):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_admin_route_allows_admin_role(client, make_user):
    admin = make_user(email="admin@university.edu", password="password123", role=UserRole.ADMIN)
    target = make_user(email="target@university.edu", password="password123")
    token = _login(client, "admin@university.edu", "password123")

    resp = client.post(
        f"/admin/users/{target.id}/verify-institution",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_institution_verified"] is True


def test_admin_route_denies_non_admin_role(client, make_user):
    make_user(email="student@university.edu", password="password123", role=UserRole.STUDENT)
    target = make_user(email="target2@university.edu", password="password123")
    token = _login(client, "student@university.edu", "password123")

    resp = client.post(
        f"/admin/users/{target.id}/verify-institution",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_admin_only_route_blocked_for_professor_too(client, make_user):
    # RBAC should block every non-admin role, not just students.
    make_user(email="prof@university.edu", password="password123", role=UserRole.PROFESSOR)
    target = make_user(email="target3@university.edu", password="password123")
    token = _login(client, "prof@university.edu", "password123")

    resp = client.post(
        f"/admin/users/{target.id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_admin_only_route_blocked_without_auth(client, make_user):
    target = make_user(email="target4@university.edu", password="password123")
    resp = client.post(f"/admin/users/{target.id}/deactivate")
    assert resp.status_code == 401


def test_deactivate_user_is_idempotent(client, make_user, db_session):
    make_user(email="admin2@university.edu", password="password123", role=UserRole.ADMIN)
    target = make_user(email="target5@university.edu", password="password123")
    token = _login(client, "admin2@university.edu", "password123")
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(f"/admin/users/{target.id}/deactivate", headers=headers)
    assert first.status_code == 200
    assert first.json()["is_active"] is False

    # Deactivating an already-deactivated user must be a no-op, not an
    # error or a duplicate state change.
    second = client.post(f"/admin/users/{target.id}/deactivate", headers=headers)
    assert second.status_code == 200
    assert second.json()["is_active"] is False

    from app.models.user import User

    stored = db_session.get(User, target.id)
    assert stored.is_active is False


def test_verify_institution_is_idempotent(client, make_user):
    make_user(email="admin3@university.edu", password="password123", role=UserRole.ADMIN)
    target = make_user(email="target6@university.edu", password="password123")
    token = _login(client, "admin3@university.edu", "password123")
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(f"/admin/users/{target.id}/verify-institution", headers=headers)
    assert first.status_code == 200
    assert first.json()["is_institution_verified"] is True

    second = client.post(f"/admin/users/{target.id}/verify-institution", headers=headers)
    assert second.status_code == 200
    assert second.json()["is_institution_verified"] is True


def test_deactivated_admin_cannot_use_admin_routes(client, make_user):
    # A deactivated account should be rejected at authentication time
    # entirely, even if it happens to hold the admin role.
    make_user(
        email="exadmin@university.edu",
        password="password123",
        role=UserRole.ADMIN,
        is_active=True,
    )
    token = _login(client, "exadmin@university.edu", "password123")

    # Now deactivate that same admin via the API using their own (still
    # valid) token, then confirm the token stops working afterwards.
    from app.models.user import User
    from app.core.enums import UserRole as _UR  # noqa: F401

    resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    user_id = resp.json()["id"]

    deactivate_resp = client.post(
        f"/admin/users/{user_id}/deactivate", headers={"Authorization": f"Bearer {token}"}
    )
    assert deactivate_resp.status_code == 200

    retry = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert retry.status_code == 403


def test_admin_action_on_unknown_user_returns_404(client, make_user):
    import uuid

    make_user(email="admin4@university.edu", password="password123", role=UserRole.ADMIN)
    token = _login(client, "admin4@university.edu", "password123")

    resp = client.post(
        f"/admin/users/{uuid.uuid4()}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
