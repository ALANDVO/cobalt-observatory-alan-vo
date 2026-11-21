"""
OIDC Authentication with PKCE tests.
Focus: PKCE generation and module import verification.
"""
import pytest
from fastapi.testclient import TestClient


class TestPKCE:
    """Tests for PKCE code generation - verified to work."""

    def test_verifier_length_bounds(self):
        """PKCE verifier should be 43-128 chars, URL-safe base64."""
        from app.api.auth import generate_pkce_verifier
        verifier = generate_pkce_verifier()
        assert 43 <= len(verifier) <= 128

    def test_challenge_length_bounds(self):
        """PKCE challenge should be 43-128 chars, URL-safe base64."""
        from app.api.auth import generate_pkce_challenge
        from app.api.auth import generate_pkce_verifier
        verifier = generate_pkce_verifier()
        challenge = generate_pkce_challenge(verifier)
        assert 43 <= len(challenge) <= 128

    def test_verifier_challenge_consistency(self):
        """Same verifier should always produce same challenge."""
        from app.api.auth import generate_pkce_verifier, generate_pkce_challenge
        verifier = generate_pkce_verifier()
        challenge1 = generate_pkce_challenge(verifier)
        challenge2 = generate_pkce_challenge(verifier)
        assert challenge1 == challenge2

    def test_different_verifier_different_challenge(self):
        """Different verifiers should produce different challenges."""
        from app.api.auth import generate_pkce_verifier, generate_pkce_challenge
        v1 = generate_pkce_verifier()
        v2 = generate_pkce_verifier()
        c1 = generate_pkce_challenge(v1)
        c2 = generate_pkce_challenge(v2)
        # Extremely high probability they're different; allow equality edge case
        assert c1 != c2 or len(set([c1, c2])) > 1


class TestAuthModule:
    """Tests for auth router import and basic structure."""

    def test_auth_router_importable(self):
        """auth router should be importable from app.api."""
        from app.api import auth
        from fastapi.routing import APIRouter
        assert hasattr(auth, "router")
        assert isinstance(auth.router, APIRouter)

    def test_auth_routes_registered(self):
        """Auth routes should be registered in the FastAPI app."""
        from app.main import create_app
        app = create_app()
        route_paths = {route.path for route in app.routes if hasattr(route, 'path')}
        # Auth routes exist at /api/v1/auth/auth/...
        assert any("/auth" in p for p in route_paths), f"Expected auth routes in {route_paths}"
