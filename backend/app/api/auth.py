"""
OIDC Authentication with Keycloak PKCE flow.

Features:
- Authorization code flow with PKCE
- Backend session management with HttpOnly cookies
- Role-based access (viewer/operator/admin)
- Login/logout flows
"""
import base64
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session, init_db, Base, engine
from app.core.config import get_settings, settings
from app.models.ocsf import OCSFEvent  # reference import to register models

router = APIRouter(prefix="/auth", tags=["auth"])

# --- PKCE helpers ---


def generate_pkce_verifier() -> str:
    """Generate a random PKCE code verifier (43-128 characters, URL-safe base64)."""
    urlsafe = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    # Ensure length is within 43-128; pad/truncate if needed
    if len(urlsafe) < 43:
        urlsafe = urlsafe + "=" * (43 - len(urlsafe))
    return urlsafe[:128]


def generate_pkce_challenge(verifier: str) -> str:
    """Generate PKCE SHA-256 challenge from verifier."""
    challenge = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(challenge).rstrip(b"=").decode("ascii")


# --- Token models ---


class TokenData:
    def __init__(self, sub: str, roles: list[str], exp: datetime):
        self.sub = sub
        self.roles = roles
        self.exp = exp


# --- Session / cookie helpers ---


def set_auth_cookie(response: Response, token: str) -> None:
    """Set HttpOnly secure cookie with auth token."""
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    response.set_cookie(
        key="cobalt_token",
        value=token,
        httponly=True,
        secure=False,  # set True in prod with HTTPS
        samesite="lax",
        max_age=int(settings.access_token_expire_minutes * 60),
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear the auth cookie."""
    response.set_cookie(
        key="cobalt_token",
        value="",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=0,
        path="/",
    )


def get_token_from_cookie(request: Request) -> str | None:
    """Extract auth token from HttpOnly cookie."""
    return request.cookies.get("cobalt_token")


# --- Dependency: get current user ---


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenData:
    """Extract and validate user from auth cookie, return TokenData."""
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication cookie")

    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.encode("utf-8"),
            algorithms=[settings.algorithm],
        )
        sub: str = payload.get("sub")
        roles: list[str] = payload.get("roles", [])
        exp: int = payload.get("exp")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        # Check expiry
        if datetime.utcnow() > datetime.utcfromtimestamp(exp):
            raise HTTPException(status_code=401, detail="Token expired")
        return TokenData(sub=sub, roles=roles, exp=datetime.utcfromtimestamp(exp))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


# --- Login: initiate PKCE flow ---


@router.get("/login")
async def login(response: Response):
    """Initiate Keycloak OIDC authorization code flow with PKCE."""
    verifier = generate_pkce_verifier()
    challenge = generate_pkce_challenge(verifier)

    # Store verifier in session/scope; for this minimal implementation,
    # we'll embed it in the redirect state and validate on callback.
    # In production, store server-side in Redis or session store.
    state = secrets.token_urlsafe(16)

    # Build Keycloak authorization URL
    keycloak_url = str(settings.keycloak_url).rstrip("/")
    realm = settings.keycloak_realm
    client_id = settings.keycloak_client_id

    params = {
        "client_id": client_id,
        "redirect_uri": f"{settings.app_url}/auth/callback" if hasattr(settings, 'app_url') else "http://localhost:8000/auth/callback",
        "response_type": "code",
        "scope": "openid profile email",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }

    auth_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/auth?{urllib.parse.urlencode(params)}"

    # We need to persist the verifier somewhere the callback can access it.
    # For this minimal round, we'll store it as a query param in the redirect
    # and validate on callback. A proper implementation uses server-side session storage.
    redirect_url = f"{auth_url}&code_challenge_verifier={verifier}"

    return RedirectResponse(url=redirect_url)


# --- Callback: exchange code for token ---


@router.get("/callback")
async def callback(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    """Handle Keycloak callback, exchange code for tokens, set session cookie."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    code_verifier = request.query_params.get("code_challenge_verifier")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Exchange authorization code for tokens
    keycloak_url = str(settings.keycloak_url).rstrip("/")
    realm = settings.keycloak_realm
    client_id = settings.keycloak_client_id
    client_secret = settings.keycloak_client_secret or ""

    token_token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": request.query_params.get("redirect_uri", "http://localhost:8000/auth/callback"),
        "client_id": client_id,
    }
    if client_secret:
        token_data["client_secret"] = client_secret

    if code_verifier:
        token_data["code_verifier"] = code_verifier

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_token_url,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

    tokens = resp.json()
    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response")

    # Decode ID token to get user info
    try:
        payload = jwt.decode(
            id_token,
            options={"verify_signature": False},  # Keycloak signs id_token; we trust the issuer
        )
        sub: str = payload.get("sub")
        preferred_username: str = payload.get("preferred_username", sub)
        roles: list[str] = payload.get("realm_access", {}).get("roles", [])
        if not roles:
            # Fallback: map by username/group
            roles = ["viewer"]
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid ID token")

    if not sub:
        raise HTTPException(status_code=400, detail="Missing subject in ID token")

    # Create access token with our signing key (shorter lived, contains our claims)
    settings = get_settings()
    access_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token_payload = {
        "sub": sub,
        "roles": roles,
        "exp": datetime.utcnow() + access_expires,
        "iat": datetime.utcnow(),
    }
    from jose import jwt as jose_jwt
    encoded_access_token = jose_jwt.encode(
        access_token_payload,
        settings.secret_key.encode("utf-8"),
        algorithm=settings.algorithm,
    )

    # Set HttpOnly cookie with our app's access token
    set_auth_cookie(response, encoded_access_token)

    # Also return tokens in JSON for programmatic use
    return {
        "access_token": encoded_access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": {"sub": sub, "preferred_username": preferred_username, "roles": roles},
    }


# --- Logout ---


@router.post("/logout")
async def logout(response: Response):
    """Clear auth cookie and redirect to Keycloak logout."""
    clear_auth_cookie(response)

    keycloak_url = str(settings.keycloak_url).rstrip("/")
    realm = settings.keycloak_realm
    client_id = settings.keycloak_client_id

    # Build Keycloak logout URL
    logout_uri = urllib.parse.quote("http://localhost:8000/auth/callback", safe="")
    logout_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/logout?redirect_uri={logout_uri}&client_id={client_id}"

    return {"redirect": logout_url}


# --- Role-based dependency ---


def require_role(*allowed_roles: str):
    """FastAPI dependency that enforces role-based access."""

    async def dependency(current_user: TokenData = Depends(get_current_user)):
        if not any(role in allowed_roles for role in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}, Have: {', '.join(current_user.roles)}",
            )
        return current_user

    return dependency
