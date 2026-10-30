"""
Evaluations API tests.
"""
import pytest


class TestEvaluations:
    """Tests for Evaluations API."""

    def test_create_evaluation(self, app):
        """Create a new evaluation."""
        # First create an agent
        agent_resp = app.post("/api/v1/agents", json={
            "name": "eval-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        eval_data = {
            "agent_id": agent_id,
            "name": "Test Evaluation",
            "dataset": "test-dataset",
            "score": 0.85,
            "metrics": {"accuracy": 0.9, "f1": 0.8},
            "details": "Test run details"
        }
        response = app.post("/api/v1/evaluations", json=eval_data)
        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["score"] == 0.85
        assert data["dataset"] == "test-dataset"

    def test_create_evaluation_invalid_agent(self, app):
        """Create evaluation with nonexistent agent fails."""
        eval_data = {
            "agent_id": 99999,
            "name": "Test",
            "dataset": "test",
            "score": 0.5,
        }
        response = app.post("/api/v1/evaluations", json=eval_data)
        assert response.status_code == 404

    def test_create_evaluation_invalid_score(self, app):
        """Create evaluation with invalid score fails."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "score-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        eval_data = {
            "agent_id": agent_id,
            "name": "Test",
            "dataset": "test",
            "score": 1.5,  # Invalid > 1.0
        }
        response = app.post("/api/v1/evaluations", json=eval_data)
        assert response.status_code == 422

    def test_list_evaluations(self, app):
        """List evaluations with pagination."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "list-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        for i in range(3):
            app.post("/api/v1/evaluations", json={
                "agent_id": agent_id,
                "name": f"Eval {i}",
                "dataset": "dataset-1",
                "score": 0.7 + i * 0.1,
            })

        response = app.get("/api/v1/evaluations?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3

    def test_filter_evaluations(self, app):
        """Filter evaluations by various criteria."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "filter-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "E1", "dataset": "ds1", "score": 0.9
        })
        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "E2", "dataset": "ds2", "score": 0.5
        })

        response = app.get(f"/api/v1/evaluations?agent_id={agent_id}&dataset=ds1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["dataset"] == "ds1"

        response = app.get(f"/api/v1/evaluations?min_score=0.8")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["score"] >= 0.8

    def test_evaluation_summary(self, app):
        """Get evaluation summary statistics."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "summary-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "E1", "dataset": "ds1", "score": 0.9
        })
        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "E2", "dataset": "ds1", "score": 0.7
        })
        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "E3", "dataset": "ds2", "score": 0.8
        })

        response = app.get("/api/v1/evaluations/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_evaluations"] == 3
        assert abs(data["average_score"] - 0.8) < 0.01
        assert data["best_score"] == 0.9
        assert data["worst_score"] == 0.7
        assert "ds1" in data["by_dataset"]
        assert "ds2" in data["by_dataset"]

    def test_get_evaluation(self, app):
        """Get evaluation by ID."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "get-eval-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        create_resp = app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "Get Eval", "dataset": "ds1", "score": 0.75
        })
        eval_id = create_resp.json()["id"]

        response = app.get(f"/api/v1/evaluations/{eval_id}")
        assert response.status_code == 200
        assert response.json()["id"] == eval_id

    def test_delete_evaluation(self, app):
        """Delete evaluation."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "del-eval-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        create_resp = app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "Del Eval", "dataset": "ds1", "score": 0.5
        })
        eval_id = create_resp.json()["id"]

        response = app.delete(f"/api/v1/evaluations/{eval_id}")
        assert response.status_code == 204

        response = app.get(f"/api/v1/evaluations/{eval_id}")
    def test_create_evaluation_with_trace(self, app):
        """Create evaluation with trace correlation."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "trace-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        trace_uid = "0af7651916cd43dd8448eb211c80319c"
        span_uid = "1234567890abcdef"
        eval_data = {
            "agent_id": agent_id,
            "name": "Trace Evaluation",
            "dataset": "trace-dataset",
            "score": 0.9,
            "trace_uid": trace_uid,
            "span_uid": span_uid,
        }
        response = app.post("/api/v1/evaluations", json=eval_data)
        assert response.status_code == 201
        data = response.json()
        assert data["trace_uid"] == trace_uid
        assert data["span_uid"] == span_uid

    def test_create_evaluation_invalid_trace_id(self, app):
        """Create evaluation with invalid trace_id fails."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "invalid-trace-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        eval_data = {
            "agent_id": agent_id,
            "name": "Invalid Trace Evaluation",
            "dataset": "trace-dataset",
            "score": 0.9,
            "trace_uid": "invalid-trace-id",
        }
        response = app.post("/api/v1/evaluations", json=eval_data)
        assert response.status_code == 422

    def test_filter_evaluations_by_trace_uid(self, app):
        """Filter evaluations by trace_uid."""
        agent_resp = app.post("/api/v1/agents", json={
            "name": "filter-trace-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = agent_resp.json()["id"]

        trace_uid_1 = "0af7651916cd43dd8448eb211c80319c"
        trace_uid_2 = "1af7651916cd43dd8448eb211c80319d"

        # Create evaluations with different trace_uids
        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "Eval 1", "dataset": "ds1", "score": 0.8,
            "trace_uid": trace_uid_1
        })
        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "Eval 2", "dataset": "ds1", "score": 0.9,
            "trace_uid": trace_uid_2
        })
        app.post("/api/v1/evaluations", json={
            "agent_id": agent_id, "name": "Eval 3", "dataset": "ds1", "score": 0.7,
            "trace_uid": trace_uid_1
        })

        # Filter by trace_uid_1
        response = app.get(f"/api/v1/evaluations?trace_uid={trace_uid_1}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["trace_uid"] == trace_uid_1

        # Filter by trace_uid_2
        response = app.get(f"/api/v1/evaluations?trace_uid={trace_uid_2}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["trace_uid"] == trace_uid_2