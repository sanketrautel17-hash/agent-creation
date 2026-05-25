# Doctor AI Monorepo

Doctor AI is an invite-only patient platform built with an `agent-360`-style monorepo layout.

## Apps and Services

- `backend/doctor_core`: main FastAPI API for auth, invites, admin, and agent sessions
- `backend/doctor_daily_transport`: reserved voice transport service for future Pipecat or Daily-specific runtime work
- `frontend`: single React app for the landing page, patient flows, and admin flows

## Local development

### Backend

```bash
cd backend/doctor_core
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

## Monorepo guidance

- Keep docs and compose files aligned with the actual folder names.
- Keep product APIs in `doctor_core`.
- Keep browser voice transport concerns isolated from product CRUD and auth logic.
