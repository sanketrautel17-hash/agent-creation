# Doctor AI Implementation Plan

## Summary

Build Doctor AI as a monorepo with separate backend services and a single frontend application.

- `backend/doctor_core` handles auth, invites, admin actions, and agent session APIs
- `backend/doctor_daily_transport` remains available for future real-time transport work
- `frontend` handles the public landing page plus patient and admin routes

The product remains invite-only for patients and uses `email + OTP` for signup and login.

## Target Repository Structure

```text
agent-creation/
|-- backend/
|   |-- doctor_core/
|   `-- doctor_daily_transport/
|-- frontend/
|   |-- public/
|   |-- src/
|   |-- package.json
|   |-- vite.config.js
|   `-- README.md
|-- docs/
|-- postman/
|-- docker-compose.yml
|-- docker-compose-core.yml
|-- docker-compose-client.yml
|-- start_all.sh
|-- stop_all.sh
`-- restart_all.sh
```

## Frontend Design

Use `frontend/` as the only web app.

Main routes:

- `/`
- `/login`
- `/invite/accept?token=...`
- `/otp`
- `/dashboard`
- `/agents/:agentType`
- `/admin`

Main responsibilities:

- public landing experience
- patient invite acceptance
- OTP login and verification
- patient dashboard and session history
- live agent session flows
- admin invite management and stats

Suggested internal structure:

- `src/pages/`
- `src/components/`
- `src/services/`
- `src/context/`
- `src/hooks/`
- `src/utils/`
- `src/styles/`

## Backend Design

### `backend/doctor_core`

Main FastAPI service responsibilities:

- invite creation and validation
- OTP send and verify
- JWT issuance and auth dependencies
- patient and admin role handling
- agent session lifecycle and history
- admin stats and invite revoke actions

### `backend/doctor_daily_transport`

Reserved for voice transport concerns when a dedicated real-time process is needed.

## Implementation Sequence

1. Keep the repo rooted at `backend/` and `frontend/`.
2. Build and maintain `backend/doctor_core/` first.
3. Keep `frontend/` as the single web app and add landing, auth, dashboard, agent, and admin routes there.
4. Add eigi session start/end integration.
5. Add `backend/doctor_daily_transport/` only if the voice pipeline needs a dedicated service.
6. Keep compose files, scripts, docs, and postman collections aligned with the actual folder layout.
