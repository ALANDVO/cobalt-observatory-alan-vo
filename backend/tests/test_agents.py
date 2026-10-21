"""
Agents API tests.
"""
import pytest


class TestAgents:
    """Tests for Agents API."""

    def test_create_agent(self, app):
        """Create a new agent."""
        agent_data = {
            "name": "test-agent",
            "description": "Test agent for evaluation",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "configuration": {"temperature": 0.7}
        }
        response = app.post("/api/v1/agents", json=agent_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-agent"
        assert data["model"] == "gpt-4o-mini"
        assert data["provider"] == "openai"
        assert data["is_active"] is True

    def test_create_duplicate_agent(self, app):
        """Creating agent with duplicate name fails."""
        agent_data = {
            "name": "duplicate-agent",
            "model": "gpt-4o-mini",
            "provider": "openai",
        }
        app.post("/api/v1/agents", json=agent_data)
        response = app.post("/api/v1/agents", json=agent_data)
        assert response.status_code == 409

    def test_list_agents(self, app):
        """List agents with pagination."""
        for i in range(3):
            app.post("/api/v1/agents", json={
                "name": f"agent-{i}",
                "model": "gpt-4o-mini",
                "provider": "openai",
            })

        response = app.get("/api/v1/agents?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3

    def test_filter_agents_by_provider(self, app):
        """Filter agents by provider."""
        app.post("/api/v1/agents", json={"name": "a1", "model": "m1", "provider": "openai"})
        app.post("/api/v1/agents", json={"name": "a2", "model": "m2", "provider": "anthropic"})

        response = app.get("/api/v1/agents?provider=openai")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["provider"] == "openai"

    def test_get_agent(self, app):
        """Get agent by ID."""
        create_resp = app.post("/api/v1/agents", json={
            "name": "get-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = create_resp.json()["id"]

        response = app.get(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "get-agent"

    def test_update_agent(self, app):
        """Update agent."""
        create_resp = app.post("/api/v1/agents", json={
            "name": "update-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = create_resp.json()["id"]

        response = app.patch(f"/api/v1/agents/{agent_id}", json={
            "model": "gpt-4o-mini",
            "description": "Updated description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4o-mini"
        assert data["description"] == "Updated description"

    def test_delete_agent(self, app):
        """Delete agent."""
        create_resp = app.post("/api/v1/agents", json={
            "name": "delete-agent", "model": "gpt-4o", "provider": "openai"
        })
        agent_id = create_resp.json()["id"]

        response = app.delete(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 204

        response = app.get(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 404