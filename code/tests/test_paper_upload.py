"""
TDD: paper upload, storage, and text-extraction behavior, defined before/
alongside the implementation in app/services/paper_service.py,
app/repositories/paper_repository.py, and app/routes/paper_routes.py.
"""
import io

from app.core.enums import PaperStatus
from tests.conftest import make_pdf_bytes


def _register_and_login(client, email="uploader@university.edu", password="password123"):
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Uploader Person", "role": "student"},
    )
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"], login.json()["user"]["id"]


def _upload(client, token, title="My Paper", abstract="An abstract.", filename="paper.pdf", co_author_ids=None, pdf_bytes=None):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"title": title, "abstract": abstract}
    if co_author_ids:
        data["co_author_ids"] = ",".join(str(i) for i in co_author_ids)
    files = {"file": (filename, io.BytesIO(pdf_bytes or make_pdf_bytes()), "application/pdf")}
    return client.post("/papers", data=data, files=files, headers=headers)


def test_upload_creates_paper_with_uploader_as_author(client, upload_dir):
    token, user_id = _register_and_login(client)

    resp = _upload(client, token, title="Deep Learning Survey")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Deep Learning Survey"
    assert body["status"] == "processing"
    assert body["file_storage_key"] is not None
    assert len(body["authors"]) == 1
    assert body["authors"][0]["id"] == user_id


def test_double_submit_does_not_create_duplicate_paper(client, upload_dir):
    token, _ = _register_and_login(client)

    first = _upload(client, token, title="Same Title Paper")
    second = _upload(client, token, title="Same Title Paper")
    assert first.status_code == 201
    assert second.status_code == 201
    # Both requests resolve to the SAME underlying paper -- the double
    # click never created a second record.
    assert first.json()["id"] == second.json()["id"]

    from app.models.paper import Paper

    # Uses the app's own db_session fixture indirectly via /papers/{id};
    # cross-checked at HTTP level too, below.
    get_resp = client.get(
        f"/papers/{first.json()['id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 200


def test_double_submit_only_creates_one_row_in_db(client, upload_dir, db_session):
    token, _ = _register_and_login(client, email="dbcheck@university.edu")

    _upload(client, token, title="DB Row Check Paper")
    _upload(client, token, title="DB Row Check Paper")

    from app.models.paper import Paper

    rows = db_session.query(Paper).filter(Paper.title == "DB Row Check Paper").all()
    assert len(rows) == 1


def test_different_titles_from_same_uploader_create_separate_papers(client, upload_dir):
    token, _ = _register_and_login(client, email="multi@university.edu")

    first = _upload(client, token, title="Paper One")
    second = _upload(client, token, title="Paper Two")
    assert first.json()["id"] != second.json()["id"]


def test_uuid_based_storage_key_never_uses_original_filename(client, upload_dir):
    token, _ = _register_and_login(client, email="filenames@university.edu")

    first = _upload(client, token, title="File A", filename="thesis.pdf")
    second = _upload(client, token, title="File B", filename="thesis.pdf")

    key_a = first.json()["file_storage_key"]
    key_b = second.json()["file_storage_key"]
    assert key_a != key_b
    assert "thesis" not in key_a
    assert "thesis" not in key_b
    assert (upload_dir / key_a).exists()
    assert (upload_dir / key_b).exists()


def test_upload_links_existing_coauthor_without_creating_duplicate_user(client, upload_dir, make_user, db_session):
    token, uploader_id = _register_and_login(client, email="lead@university.edu")
    coauthor = make_user(email="coauthor@university.edu", password="password123")

    resp = _upload(client, token, title="Collaborative Paper", co_author_ids=[coauthor.id])
    assert resp.status_code == 201, resp.text
    author_ids = {a["id"] for a in resp.json()["authors"]}
    assert author_ids == {uploader_id, str(coauthor.id)}

    from app.models.user import User

    assert db_session.query(User).filter(User.email == "coauthor@university.edu").count() == 1


def test_upload_with_unknown_coauthor_id_is_skipped_not_errored(client, upload_dir):
    import uuid

    token, uploader_id = _register_and_login(client, email="lonewolf@university.edu")
    resp = _upload(client, token, title="Solo-ish Paper", co_author_ids=[uuid.uuid4()])
    assert resp.status_code == 201, resp.text
    assert [a["id"] for a in resp.json()["authors"]] == [uploader_id]


def test_upload_requires_authentication(client, upload_dir):
    files = {"file": ("paper.pdf", io.BytesIO(make_pdf_bytes()), "application/pdf")}
    resp = client.post("/papers", data={"title": "No Auth Paper", "abstract": "x"}, files=files)
    assert resp.status_code == 401


def test_extract_text_populates_extracted_text(client, upload_dir):
    token, _ = _register_and_login(client, email="extract1@university.edu")
    upload = _upload(
        client, token, title="Extraction Target", pdf_bytes=make_pdf_bytes("Unique Marker Text")
    )
    paper_id = upload.json()["id"]
    assert upload.json()["extracted_text"] is None

    resp = client.post(
        f"/papers/{paper_id}/extract-text", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    assert "Unique Marker Text" in resp.json()["extracted_text"]


def test_reextraction_overwrites_rather_than_duplicates(client, upload_dir, db_session):
    token, _ = _register_and_login(client, email="extract2@university.edu")
    upload = _upload(
        client, token, title="Reprocessed Paper", pdf_bytes=make_pdf_bytes("Original Content")
    )
    paper_id = upload.json()["id"]
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(f"/papers/{paper_id}/extract-text", headers=headers)
    second = client.post(f"/papers/{paper_id}/extract-text", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200

    import uuid

    from app.models.paper import Paper

    rows = db_session.query(Paper).filter(Paper.id == uuid.UUID(paper_id)).all()
    # Still exactly one row for this paper...
    assert len(rows) == 1
    # ...and the text wasn't appended to itself on the second run.
    text = second.json()["extracted_text"]
    assert text.count("Original Content") == 1


def test_extract_text_on_unknown_paper_returns_404(client, upload_dir):
    import uuid

    token, _ = _register_and_login(client, email="extract3@university.edu")
    resp = client.post(
        f"/papers/{uuid.uuid4()}/extract-text", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def test_search_users_for_coauthor_tagging(client, upload_dir, make_user):
    token, _ = _register_and_login(client, email="searcher@university.edu")
    make_user(email="ada.lovelace@university.edu", password="password123", full_name="Ada Lovelace")
    make_user(email="grace.hopper@university.edu", password="password123", full_name="Grace Hopper")

    resp = client.get(
        "/users/search", params={"q": "Ada"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    names = [u["full_name"] for u in resp.json()]
    assert "Ada Lovelace" in names
    assert "Grace Hopper" not in names


def test_search_users_requires_authentication(client, upload_dir):
    resp = client.get("/users/search", params={"q": "a"})
    assert resp.status_code == 401
