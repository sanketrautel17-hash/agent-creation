# Architecture Decision Record Log

## ADR-001: Monorepo shape

Adopt an `agent-360`-style monorepo with named backend services and frontend apps instead of a single flat backend app and a single flat frontend folder.

## ADR-002: Auth model

Use invite-gated patient access with OTP-only signup and OTP-only returning login. Seed admins directly in MongoDB for v1.

## ADR-003: Frontend split

Keep one authenticated client app for both patient and admin routes, plus one public landing page app.
