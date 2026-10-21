"""
Health endpoint tests.
"""
import pytest


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, app):
        """Test basic health check."""
        response = app.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cobalt-observatory"

    def test_health_check_db(self, app):
        """Test database health check."""
        response = app.get("/api/v1/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"