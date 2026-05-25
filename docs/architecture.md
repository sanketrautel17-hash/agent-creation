# Doctor AI Architecture

## Monorepo layout

- `backend/doctor_core`
  - main FastAPI API and business logic
- `backend/doctor_daily_transport`
  - optional dedicated transport service for real-time voice runtime concerns
- `frontend`
  - single React app that serves the landing page plus patient and admin experiences

## Backend layers

`doctor_core` follows:

- routes
- schemas
- controllers
- services
- cruds
- models
- database
- config
- utils

## Core flows

- invite-only patient onboarding
- OTP signup and login
- seeded admin OTP login
- eigi session start and end bridge
- patient session history and admin stats
