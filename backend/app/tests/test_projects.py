def test_create_project_success(client, auth_headers):
    headers = auth_headers()
    resp = client.post("/projects", json={"name": "Project A", "description": "desc"}, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Project A"
    assert body["is_archived"] is False


def test_create_project_requires_auth(client):
    resp = client.post("/projects", json={"name": "Project A"})
    assert resp.status_code == 401


def test_create_project_duplicate_name(client, auth_headers):
    headers = auth_headers()
    client.post("/projects", json={"name": "Dup Project"}, headers=headers)
    resp = client.post("/projects", json={"name": "Dup Project"}, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["error"] == "Project name already exists"


def test_create_project_blank_name(client, auth_headers):
    headers = auth_headers()
    resp = client.post("/projects", json={"name": "   "}, headers=headers)
    assert resp.status_code == 422


def test_list_projects(client, auth_headers):
    headers = auth_headers()
    client.post("/projects", json={"name": "Project List 1"}, headers=headers)
    client.post("/projects", json={"name": "Project List 2"}, headers=headers)
    resp = client.get("/projects", headers=headers)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert "Project List 1" in names
    assert "Project List 2" in names


def test_get_project_not_found(client, auth_headers):
    headers = auth_headers()
    resp = client.get("/projects/99999", headers=headers)
    assert resp.status_code == 404


def test_get_project_forbidden_for_other_user(client, auth_headers):
    headers_a = auth_headers(email="ownerA@example.com")
    create_resp = client.post("/projects", json={"name": "Owner A Project"}, headers=headers_a)
    project_id = create_resp.json()["id"]

    headers_b = auth_headers(email="ownerB@example.com")
    resp = client.get(f"/projects/{project_id}", headers=headers_b)
    assert resp.status_code == 403


def test_update_project_name(client, auth_headers):
    headers = auth_headers()
    create_resp = client.post("/projects", json={"name": "Old Name"}, headers=headers)
    project_id = create_resp.json()["id"]

    resp = client.patch(f"/projects/{project_id}", json={"name": "New Name"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_archive_and_unarchive_project(client, auth_headers):
    headers = auth_headers()
    create_resp = client.post("/projects", json={"name": "Archivable"}, headers=headers)
    project_id = create_resp.json()["id"]

    archive_resp = client.post(f"/projects/{project_id}/archive", headers=headers)
    assert archive_resp.status_code == 200
    assert archive_resp.json()["is_archived"] is True

    unarchive_resp = client.post(f"/projects/{project_id}/unarchive", headers=headers)
    assert unarchive_resp.status_code == 200
    assert unarchive_resp.json()["is_archived"] is False


def test_archived_projects_excluded_by_default(client, auth_headers):
    headers = auth_headers()
    create_resp = client.post("/projects", json={"name": "ToArchive"}, headers=headers)
    project_id = create_resp.json()["id"]
    client.post(f"/projects/{project_id}/archive", headers=headers)

    resp = client.get("/projects", headers=headers)
    names = [p["name"] for p in resp.json()]
    assert "ToArchive" not in names

    resp_with_archived = client.get("/projects?include_archived=true", headers=headers)
    names_with_archived = [p["name"] for p in resp_with_archived.json()]
    assert "ToArchive" in names_with_archived
