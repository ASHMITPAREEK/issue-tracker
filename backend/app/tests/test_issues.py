def _create_project(client, headers, name="Issue Project"):
    resp = client.post("/projects", json={"name": name}, headers=headers)
    return resp.json()["id"]


def test_create_issue_success(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)

    resp = client.post(
        "/issues",
        json={"title": "Bug 1", "project_id": project_id, "priority": "High"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Bug 1"
    assert body["status"] == "Todo"
    assert body["priority"] == "High"


def test_create_issue_requires_auth(client):
    resp = client.post("/issues", json={"title": "Bug 1", "project_id": 1})
    assert resp.status_code == 401


def test_create_issue_blank_title(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    resp = client.post("/issues", json={"title": "  ", "project_id": project_id}, headers=headers)
    assert resp.status_code == 422


def test_create_issue_invalid_project(client, auth_headers):
    headers = auth_headers()
    resp = client.post("/issues", json={"title": "Bug 1", "project_id": 99999}, headers=headers)
    assert resp.status_code == 404


def test_create_issue_invalid_priority(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    resp = client.post(
        "/issues", json={"title": "Bug 1", "project_id": project_id, "priority": "Urgent"}, headers=headers
    )
    assert resp.status_code == 422


def test_create_issue_invalid_assignee(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    resp = client.post(
        "/issues",
        json={"title": "Bug 1", "project_id": project_id, "assignee_id": 99999},
        headers=headers,
    )
    assert resp.status_code == 400


def test_list_issues_filter_by_status(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    client.post("/issues", json={"title": "Todo Issue", "project_id": project_id}, headers=headers)
    done_resp = client.post(
        "/issues", json={"title": "Done Issue", "project_id": project_id, "status": "Done"}, headers=headers
    )
    issue_id = done_resp.json()["id"]
    client.patch(f"/issues/{issue_id}", json={"status": "Done"}, headers=headers)

    resp = client.get(f"/issues?project_id={project_id}&status=Done", headers=headers)
    titles = [i["title"] for i in resp.json()]
    assert "Done Issue" in titles
    assert "Todo Issue" not in titles


def test_list_issues_search_by_title(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    client.post("/issues", json={"title": "Login button broken", "project_id": project_id}, headers=headers)
    client.post("/issues", json={"title": "Dashboard chart missing", "project_id": project_id}, headers=headers)

    resp = client.get(f"/issues?project_id={project_id}&search=login", headers=headers)
    titles = [i["title"] for i in resp.json()]
    assert any("Login" in t for t in titles)
    assert all("Dashboard" not in t for t in titles)


def test_list_issues_filter_by_priority(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    client.post(
        "/issues", json={"title": "Critical bug", "project_id": project_id, "priority": "Critical"}, headers=headers
    )
    client.post(
        "/issues", json={"title": "Low priority", "project_id": project_id, "priority": "Low"}, headers=headers
    )

    resp = client.get(f"/issues?project_id={project_id}&priority=Critical", headers=headers)
    titles = [i["title"] for i in resp.json()]
    assert "Critical bug" in titles
    assert "Low priority" not in titles


def test_update_issue_status(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    create_resp = client.post("/issues", json={"title": "Status test", "project_id": project_id}, headers=headers)
    issue_id = create_resp.json()["id"]

    resp = client.patch(f"/issues/{issue_id}", json={"status": "In Progress"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "In Progress"


def test_update_issue_invalid_status(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    create_resp = client.post("/issues", json={"title": "Status test", "project_id": project_id}, headers=headers)
    issue_id = create_resp.json()["id"]

    resp = client.patch(f"/issues/{issue_id}", json={"status": "Blocked"}, headers=headers)
    assert resp.status_code == 422


def test_assign_issue(client, auth_headers):
    headers = auth_headers(email="assigner@example.com")
    me_resp = client.get("/auth/me", headers=headers)
    user_id = me_resp.json()["id"]

    project_id = _create_project(client, headers)
    create_resp = client.post("/issues", json={"title": "Assign me", "project_id": project_id}, headers=headers)
    issue_id = create_resp.json()["id"]

    resp = client.patch(f"/issues/{issue_id}", json={"assignee_id": user_id}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["assignee"]["id"] == user_id


def test_delete_issue(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    create_resp = client.post("/issues", json={"title": "Delete me", "project_id": project_id}, headers=headers)
    issue_id = create_resp.json()["id"]

    resp = client.delete(f"/issues/{issue_id}", headers=headers)
    assert resp.status_code == 204

    get_resp = client.get(f"/issues/{issue_id}", headers=headers)
    assert get_resp.status_code == 404


def test_issue_not_found(client, auth_headers):
    headers = auth_headers()
    resp = client.get("/issues/99999", headers=headers)
    assert resp.status_code == 404


def test_issue_forbidden_for_other_user(client, auth_headers):
    headers_a = auth_headers(email="issueOwnerA@example.com")
    project_id = _create_project(client, headers_a, name="A's Project")
    create_resp = client.post("/issues", json={"title": "A's Issue", "project_id": project_id}, headers=headers_a)
    issue_id = create_resp.json()["id"]

    headers_b = auth_headers(email="issueOwnerB@example.com")
    resp = client.get(f"/issues/{issue_id}", headers=headers_b)
    assert resp.status_code == 403


def test_dashboard_stats(client, auth_headers):
    headers = auth_headers()
    project_id = _create_project(client, headers)
    client.post("/issues", json={"title": "Open issue", "project_id": project_id}, headers=headers)
    done_resp = client.post(
        "/issues", json={"title": "Done issue", "project_id": project_id}, headers=headers
    )
    client.patch(f"/issues/{done_resp.json()['id']}", json={"status": "Done"}, headers=headers)

    resp = client.get("/dashboard/stats", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_projects"] == 1
    assert body["total_issues"] == 2
    assert body["open_issues"] == 1
    assert body["completed_issues"] == 1
