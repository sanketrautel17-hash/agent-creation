# Doctor Core

Main FastAPI service for the Doctor AI monorepo.

## Responsibilities

- invite creation and validation
- OTP signup and login
- admin authentication and patient access control
- JWT issuance and user session restoration
- eigi session start and end orchestration
- patient session history and admin stats

## Run locally

```bash
uvicorn main:app --reload --port 8000
```

## Required env for voice sessions

The voice bridge needs these values in `backend/.env`:

- `EIGI_API_KEY`
- `EIGI_APPOINTMENT_AGENT_ID`
- `EIGI_FOLLOWUP_AGENT_ID`
- `EIGI_PRESCRIPTION_AGENT_ID`

Use [backend/.env.example](/C:/Users/munna/my_projects/agent-creation/backend/.env.example) as the template for local setup.
