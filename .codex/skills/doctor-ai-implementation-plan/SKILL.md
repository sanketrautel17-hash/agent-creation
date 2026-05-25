---
name: doctor-ai-implementation-plan
description: Implement or extend the Doctor AI project in this repository while preserving an agent-360-style monorepo structure. Use when Codex needs to build or refactor the FastAPI backend services, React frontend apps, invite-only OTP auth flow, admin invite management, MongoDB models, project docs, docker-compose layout, or eigi/Pipecat voice integration for this doctor and patient platform.
---

# Doctor AI Implementation Plan

## Overview

Implement the project as a monorepo shaped like `agent-360`, not as a single flat backend app plus a single flat frontend app. Preserve the top-level `backend/` and `frontend/` directories, but organize the real application into service-style subfolders, shared docs, and deployment entrypoints.

## Core Product Rules

- Keep the product invite-only for patients.
- Use `email + OTP` for first-time signup after invite acceptance.
- Use `email + OTP` for all returning patient logins.
- Seed admin users directly in MongoDB for v1.
- Use Gmail SMTP first for invite and OTP delivery.
- Integrate the real `eigi.ai` session flow for voice sessions.
- Keep patient Google login out of scope unless the user explicitly changes the requirements.

## Target Monorepo Shape

Build toward this repo shape:

- `backend/doctor_core/`
- `backend/doctor_daily_transport/`
- `frontend/client_frontend/`
- `frontend/landing_page/`
- `docs/`
- `docs/decisions/`
- `docs/implementation-guide/`
- `postman/`
- `docker-compose.yml`
- `docker-compose-core.yml`
- `docker-compose-client.yml`
- `docker-compose-landing.yml`
- `start_all.sh`, `stop_all.sh`, `restart_all.sh`

Do not keep the long-term implementation in the current root-level `backend/main.py` and `backend/core/...` scaffold. Migrate that scaffold into `backend/doctor_core/` so the repository shape stays consistent with the service-based pattern.

## Backend Services

### `backend/doctor_core/`

Use this as the main FastAPI service. Follow the layered layout used in `agent-360`:

- `main.py`
- `requirements.txt`
- `Dockerfile`
- `README.md`
- `core/apis/routes/`
- `core/apis/schemas/`
- `core/controllers/`
- `core/services/`
- `core/cruds/`
- `core/models/`
- `core/database/`
- `core/config/`
- `core/utils/`
- `tests/`

Place the invite system, OTP auth, admin actions, JWT handling, MongoDB access, and agent session history in this service.

### `backend/doctor_daily_transport/`

Use this service for the real-time web voice transport layer if the implementation needs a dedicated Pipecat or Daily bridge instead of placing all voice logic in `doctor_core`.

- Keep session transport concerns here.
- Keep browser voice session wiring here.
- Keep provider-specific voice pipeline utilities here.
- Keep `doctor_core` focused on product APIs, users, invites, and session metadata.

If the first iteration does not need a separate transport process, still reserve this folder and document whether it is active, deferred, or implemented as a thin bridge.

## Frontend Apps

### `frontend/client_frontend/`

Use this as the main authenticated React app for:

- patient login
- invite signup
- OTP verification
- patient dashboard
- live agent sessions
- admin panel

Keep the admin experience inside this app as role-gated routes instead of creating a separate admin frontend unless the user explicitly requests a split app.

### `frontend/landing_page/`

Use this as the public marketing and clinic onboarding site:

- hero and product explanation
- doctor/clinic branding
- sign-in and invite CTA entrypoints
- optionally static help or contact sections

## Main Functional Areas

### Auth and invite flow

Implement these behaviors inside `doctor_core`:

1. Admin creates an invite for a patient email.
2. Patient opens `/invite/accept?token=...`.
3. Backend validates the token before OTP send.
4. Frontend prefills email and collects full name.
5. OTP send succeeds only for valid, non-revoked, non-expired invites.
6. OTP verify creates the patient if needed, activates the invite, issues JWT, and routes to the dashboard.
7. Returning patients use `email + OTP` from `/login` without a new invite.

### Admin flow

- Reuse OTP login for admins.
- Skip invite validation for seeded admin accounts.
- Protect admin routes through JWT and role checks.
- Let admins create invites, list invites, revoke invites, and view patient/session stats.

### Agent flow

- Start the voice session through backend APIs first.
- Map doctor agent types to configured eigi IDs.
- Return session credentials to the client app.
- End sessions through backend APIs and persist transcript, summary, and duration.

## Data Model

Create and maintain these collections:

- `users`
- `invites`
- `otp_sessions`
- `agent_sessions`

Required enums:

- `UserRole = patient | admin`
- `InviteStatus = pending | activated | expired | revoked`
- `OtpPurpose = signup | login`
- `AgentType = appointment | followup | prescription`

Keep indexes explicit and close to the data layer:

- unique normalized email on `users`
- one active invite per email policy
- TTL on `otp_sessions.expires_at`

## API Contract

Implement these core routes in `doctor_core`:

- `POST /api/auth/send-otp`
- `POST /api/auth/verify-otp`
- `GET /api/auth/me`
- `GET /api/invites/accept`
- `POST /api/admin/invites`
- `GET /api/admin/invites`
- `DELETE /api/admin/invites/{invite_id}`
- `GET /api/admin/stats`
- `POST /api/agents/start-session`
- `POST /api/agents/end-session`
- `GET /api/agents/history`

Use Pydantic request and response models in `core/apis/schemas/`.

## Security and Provider Rules

- Generate 6-digit OTPs.
- Hash OTPs before storage.
- Expire OTPs after 10 minutes.
- Block verification after 3 failed attempts.
- Invalidate prior unverified OTP sessions on resend.
- Restrict CORS to configured frontend origins.
- Normalize emails to lowercase everywhere.
- Avoid logging raw OTPs, JWTs, invite tokens, or provider secrets.
- Keep Gmail SMTP behind an email service abstraction.
- Keep eigi session operations behind a narrow service interface.

## Docs and Operational Files

Keep project guidance close to the repo shape used in `agent-360`:

- `docs/architecture.md`
- `docs/implementation-guide/DOCTOR_AI_IMPLEMENTATION_PLAN.md`
- `docs/decisions/adr.md` or targeted ADR files as needed
- `postman/` collections for key auth, admin, and agent APIs

Keep root operational scripts and compose files aligned with real folders and service names. Do not let scripts or README references drift away from the actual repo layout.

## Suggested Build Order

1. Restructure the repo into the monorepo layout first.
2. Build `backend/doctor_core/` with config, database, models, CRUDs, services, controllers, routes, and tests.
3. Add the invite and OTP auth flow.
4. Add admin invite management and stats.
5. Scaffold `frontend/client_frontend/` with auth, patient, and admin routes.
6. Scaffold `frontend/landing_page/`.
7. Add real eigi session start/end integration.
8. Add `backend/doctor_daily_transport/` if a dedicated real-time transport service is required.
9. Add docs, compose files, and startup scripts that match the actual structure.

## Validation Checklist

- invited email can request signup OTP with a valid invite token
- expired, revoked, or unknown invites cannot start signup
- successful signup creates the patient and activates the invite
- returning patient can log in with OTP only
- patient JWT cannot access admin routes
- admin can create and revoke invites
- revoked patient cannot request a new OTP
- session start persists a local record and handles eigi errors cleanly
- session end stores transcript and duration
- root scripts and compose files reference real folders and real service names
- README and docs describe the same structure that exists on disk

## Assumptions

- Keep MongoDB as the only persistence layer for v1.
- Keep refresh tokens, audit logs, and medical record features out of scope unless requested.
- Prefer one authenticated frontend app plus one public landing app.
- Prefer one main backend service plus an optional dedicated voice transport service.
- Treat repo-structure consistency as a first-class requirement, not a documentation afterthought.
