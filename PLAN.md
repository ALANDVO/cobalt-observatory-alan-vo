# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

continue-implementation

## Roadmap

### continue-implementation — Continue implementation and resolve known failures

Status: done

Acceptance:
- Run checks, fix failures, and implement the next planned feature

Implementation: `backend/app/api/__init__.py`, `backend/app/models/ocsf.py`, `backend/app/main.py`, `backend/app/core/database.py`, `frontend/package.json (added @testing-library/dom)`

Tests: `backend/tests/test_health.py`, `backend/tests/test_ocsf_events.py`, `backend/tests/test_agents.py`, `backend/tests/test_evaluations.py`, `backend/tests/test_llm.py`, `frontend/__tests__/pages.test.tsx`

### auth-oidc — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Authorization code flow with PKCE
- Backend session management with HttpOnly cookies
- Role-based access (viewer/operator/admin)
- Login/logout flows work end-to-end

### docs-packaging — Documentation, packaging, and CI completion

Status: planned

Acceptance:
- README with Mermaid architecture diagram
- CHANGELOG.md, LICENSE, .env.example
- CI passes backend (12+ tests) and frontend (3+ tests)
- Dockerfiles with nonroot users, healthchecks
- Source code within 50-150KB budget

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
