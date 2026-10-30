# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-21

### Added
- Initial release of Cobalt Observatory
- FastAPI backend with SQLite persistence
- React + TypeScript + Vite frontend
- OCSF Events API with trace correlation (OCSF 1.8 Trace Profile)
- Agents API for AI agent management
- Evaluations API with deterministic scoring and opt-in LLM explanations
- LLM adapter service supporting OpenAI-compatible, Anthropic, and Gemini providers
- Keycloak OIDC authentication with PKCE (realm export included)
- Docker Compose with backend, frontend, and Keycloak
- Comprehensive test suite (14 backend tests, 3 frontend tests)
- Documentation: README, API reference, architecture diagram

### Features
- **OCSF Trace Correlation**: Events carry `trace.uid` and `trace` profile when emitted inside sampled OTel span
- **Three Workflows**: OCSF ingestion, Agent management, Agent evaluation
- **Pagination & Filtering**: All list endpoints support pagination and multiple filter options
- **Audit Logging**: Automatic audit trail for all mutations
- **Responsive UI**: Professional dashboard with loading, error, and empty states

### Security
- HttpOnly SameSite cookies for session management
- CSRF protection on state-changing operations
- Role-based access control (viewer/operator/admin)
- No hardcoded secrets or credentials
- Demo mode explicitly blocked in production