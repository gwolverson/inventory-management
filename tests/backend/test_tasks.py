"""
Tests for tasks API endpoints.
"""
import pytest


class TestTasksEndpoints:
    """Test suite for task-related endpoints (CRUD over in-memory tasks)."""

    def test_get_all_tasks(self, client):
        """Test getting all tasks returns a list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task_success(self, client):
        """Test creating a task returns it with a generated id and pending status."""
        payload = {"title": "Review Q3 inventory", "priority": "high", "dueDate": "2026-08-01"}
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Review Q3 inventory"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-08-01"
        assert task["status"] == "pending"
        # Ids are strings so they never collide with the frontend's numeric mock ids.
        assert isinstance(task["id"], str)

    def test_create_task_defaults_priority_to_medium(self, client):
        """Test that priority defaults to medium when omitted."""
        payload = {"title": "Task without priority", "dueDate": "2026-08-05"}
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_task_trims_title(self, client):
        """Test that surrounding whitespace is stripped from the title."""
        payload = {"title": "  Trim me  ", "priority": "low", "dueDate": "2026-08-05"}
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 201
        assert response.json()["title"] == "Trim me"

    def test_create_task_blank_title_rejected(self, client):
        """Test that a blank/whitespace-only title is rejected with 400."""
        payload = {"title": "   ", "priority": "low", "dueDate": "2026-08-05"}
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_create_task_missing_required_fields(self, client):
        """Test that omitting required fields fails validation with 422."""
        response = client.post("/api/tasks", json={"priority": "low"})
        assert response.status_code == 422

    def test_created_task_appears_in_list(self, client):
        """Test that a created task is retrievable via GET."""
        payload = {"title": "Appears in list", "priority": "medium", "dueDate": "2026-08-09"}
        created = client.post("/api/tasks", json=payload).json()

        all_tasks = client.get("/api/tasks").json()
        matching = [t for t in all_tasks if t["id"] == created["id"]]
        assert len(matching) == 1
        assert matching[0]["title"] == "Appears in list"

    def test_created_task_is_newest_first(self, client):
        """Test that a newly created task is placed at the front of the list."""
        payload = {"title": "Newest task", "priority": "high", "dueDate": "2026-08-12"}
        created = client.post("/api/tasks", json=payload).json()

        all_tasks = client.get("/api/tasks").json()
        assert all_tasks[0]["id"] == created["id"]

    def test_toggle_task_flips_status(self, client):
        """Test that PATCH toggles a task between pending and completed."""
        created = client.post(
            "/api/tasks",
            json={"title": "Toggle me", "priority": "low", "dueDate": "2026-08-15"},
        ).json()
        task_id = created["id"]
        assert created["status"] == "pending"

        toggled = client.patch(f"/api/tasks/{task_id}")
        assert toggled.status_code == 200
        assert toggled.json()["status"] == "completed"

        toggled_again = client.patch(f"/api/tasks/{task_id}")
        assert toggled_again.status_code == 200
        assert toggled_again.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test that toggling a task that doesn't exist returns 404."""
        response = client.patch("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_delete_task_success(self, client):
        """Test that a task can be deleted and is then gone from the list."""
        created = client.post(
            "/api/tasks",
            json={"title": "Delete me", "priority": "medium", "dueDate": "2026-08-20"},
        ).json()
        task_id = created["id"]

        delete_response = client.delete(f"/api/tasks/{task_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        all_tasks = client.get("/api/tasks").json()
        assert all(t["id"] != task_id for t in all_tasks)

    def test_delete_nonexistent_task(self, client):
        """Test that deleting a task that doesn't exist returns 404."""
        response = client.delete("/api/tasks/task-nonexistent-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_task_ids_are_unique_across_deletions(self, client):
        """Test that ids stay unique even after deletions create gaps."""
        first = client.post(
            "/api/tasks",
            json={"title": "First", "priority": "low", "dueDate": "2026-08-01"},
        ).json()
        client.delete(f"/api/tasks/{first['id']}")

        second = client.post(
            "/api/tasks",
            json={"title": "Second", "priority": "low", "dueDate": "2026-08-02"},
        ).json()

        # A monotonic counter means the reused slot does not reuse the old id.
        assert second["id"] != first["id"]
