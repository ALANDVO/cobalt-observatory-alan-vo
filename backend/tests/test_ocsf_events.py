"""
OCSF Events API tests.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4


class TestOCSFEvents:
    """Tests for OCSF Events API."""

    def test_create_ocsf_event_minimal(self, app):
        """Create OCSF event with minimal required fields."""
        event_data = {
            "class_uid": 4001,
            "activity_id": 1,
            "category_uid": 4,
            "category_name": "Network Activity",
            "class_name": "Network Connection",
            "time": datetime.now(timezone.utc).isoformat(),
            "severity_id": 1,
            "severity": "Informational",
            "status_id": 1,
            "status": "Success",
        }
        response = app.post("/api/v1/ocsf/events", json=event_data)
        assert response.status_code == 201
        data = response.json()
        assert data["class_uid"] == 4001
        assert data["activity_id"] == 1
        assert data["trace_uid"] is None
        assert data["trace_profile"] is False

    def test_create_ocsf_event_with_trace(self, app):
        """Create OCSF event with trace correlation."""
        event_data = {
            "class_uid": 4001,
            "activity_id": 1,
            "category_uid": 4,
            "category_name": "Network Activity",
            "class_name": "Network Connection",
            "time": datetime.now(timezone.utc).isoformat(),
            "severity_id": 1,
            "severity": "Informational",
            "status_id": 1,
            "status": "Success",
            "trace_context": {
                "uid": "0af7651916cd43dd8448eb211c80319c",
                "span_id": "1234567890abcdef"
            },
            "profiles": ["security_control", "network_proxy"]
        }
        response = app.post("/api/v1/ocsf/events", json=event_data)
        assert response.status_code == 201
        data = response.json()
        assert data["trace_uid"] == "0af7651916cd43dd8448eb211c80319c"
        assert data["span_uid"] == "1234567890abcdef"
        assert data["trace_profile"] is True
        assert "trace" in data["profiles"]
        assert "security_control" in data["profiles"]
        assert "network_proxy" in data["profiles"]

    def test_create_ocsf_event_invalid_trace_id(self, app):
        """Test validation rejects invalid trace ID format."""
        event_data = {
            "class_uid": 4001,
            "activity_id": 1,
            "category_uid": 4,
            "category_name": "Network Activity",
            "class_name": "Network Connection",
            "time": datetime.now(timezone.utc).isoformat(),
            "severity_id": 1,
            "severity": "Informational",
            "status_id": 1,
            "status": "Success",
            "trace_context": {
                "uid": "invalid-trace-id",
            }
        }
        response = app.post("/api/v1/ocsf/events", json=event_data)
        assert response.status_code == 422

    def test_list_ocsf_events_empty(self, app):
        """List events when empty."""
        response = app.get("/api/v1/ocsf/events")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_ocsf_events_with_pagination(self, app):
        """List events with pagination."""
        # Create multiple events
        for i in range(5):
            event_data = {
                "class_uid": 4001,
                "activity_id": 1,
                "category_uid": 4,
                "category_name": "Network Activity",
                "class_name": "Network Connection",
                "time": datetime.now(timezone.utc).isoformat(),
                "severity_id": 1,
                "severity": "Informational",
                "status_id": 1,
                "status": "Success",
            }
            app.post("/api/v1/ocsf/events", json=event_data)

        response = app.get("/api/v1/ocsf/events?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    def test_filter_by_trace_uid(self, app):
        """Filter events by trace UID."""
        trace_uid = "0af7651916cd43dd8448eb211c80319c"
        other_trace = "11111111111111111111111111111111"

        # Create events with different trace UIDs
        for uid in [trace_uid, trace_uid, other_trace]:
            event_data = {
                "class_uid": 4001,
                "activity_id": 1,
                "category_uid": 4,
                "category_name": "Network Activity",
                "class_name": "Network Connection",
                "time": datetime.now(timezone.utc).isoformat(),
                "severity_id": 1,
                "severity": "Informational",
                "status_id": 1,
                "status": "Success",
                "trace_context": {"uid": uid},
            }
            app.post("/api/v1/ocsf/events", json=event_data)

        response = app.get(f"/api/v1/ocsf/events?trace_uid={trace_uid}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(e["trace_uid"] == trace_uid for e in data["items"])

    def test_filter_by_has_trace(self, app):
        """Filter events by trace presence."""
        # Event with trace
        app.post("/api/v1/ocsf/events", json={
            "class_uid": 4001, "activity_id": 1, "category_uid": 4,
            "category_name": "Network", "class_name": "Connection",
            "time": datetime.now(timezone.utc).isoformat(),
            "severity_id": 1, "severity": "Info", "status_id": 1, "status": "Success",
            "trace_context": {"uid": "0af7651916cd43dd8448eb211c80319c"},
        })
        # Event without trace
        app.post("/api/v1/ocsf/events", json={
            "class_uid": 4001, "activity_id": 1, "category_uid": 4,
            "category_name": "Network", "class_name": "Connection",
            "time": datetime.now(timezone.utc).isoformat(),
            "severity_id": 1, "severity": "Info", "status_id": 1, "status": "Success",
        })

        response = app.get("/api/v1/ocsf/events?has_trace=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["trace_uid"] is not None

        response = app.get("/api/v1/ocsf/events?has_trace=false")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["trace_uid"] is None

    def test_get_event_by_trace_endpoint(self, app):
        """Test dedicated trace lookup endpoint."""
        trace_uid = "0af7651916cd43dd8448eb211c80319c"
        for i in range(3):
            app.post("/api/v1/ocsf/events", json={
                "class_uid": 4001, "activity_id": 1, "category_uid": 4,
                "category_name": "Network", "class_name": "Connection",
                "time": datetime.now(timezone.utc).isoformat(),
                "severity_id": 1, "severity": "Info", "status_id": 1, "status": "Success",
                "trace_context": {"uid": trace_uid},
            })

        response = app.get(f"/api/v1/ocsf/events/trace/{trace_uid}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(e["trace_uid"] == trace_uid for e in data)

    def test_get_single_event(self, app):
        """Get single event by ID."""
        create_resp = app.post("/api/v1/ocsf/events", json={
            "class_uid": 4001, "activity_id": 1, "category_uid": 4,
            "category_name": "Network", "class_name": "Connection",
            "time": datetime.now(timezone.utc).isoformat(),
            "severity_id": 1, "severity": "Info", "status_id": 1, "status": "Success",
        })
        event_id = create_resp.json()["id"]

        response = app.get(f"/api/v1/ocsf/events/{event_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id

    def test_get_nonexistent_event(self, app):
        """Get nonexistent event returns 404."""
        response = app.get("/api/v1/ocsf/events/99999")
        assert response.status_code == 404

    def test_delete_event(self, app):
        """Delete an event."""
        create_resp = app.post("/api/v1/ocsf/events", json={
            "class_uid": 4001, "activity_id": 1, "category_uid": 4,
            "category_name": "Network", "class_name": "Connection",
            "time": datetime.now(timezone.utc).isoformat(),
            "severity_id": 1, "severity": "Info", "status_id": 1, "status": "Success",
        })
        event_id = create_resp.json()["id"]

        response = app.delete(f"/api/v1/ocsf/events/{event_id}")
        assert response.status_code == 204

        # Verify deleted
        response = app.get(f"/api/v1/ocsf/events/{event_id}")
        assert response.status_code == 404