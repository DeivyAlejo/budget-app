# Budget App

Full-stack budget tracker to manage monthly spending with personal accounts.

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic, SQLite (PostgreSQL-ready)
- Frontend: React + TypeScript + Vite

## Project Structure

- backend/: FastAPI API and data layer
- frontend/: React web application
- docs/: planning and project docs

## Getting Started

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API base URL (local machine): http://localhost:8000
Health check: http://localhost:8000/api/v1/health

### 2) Frontend

```bash
cd frontend
npm run dev
```

Frontend URL (local machine): http://localhost:5173

## Access From Another Computer On LAN

1. Start backend with host 0.0.0.0 and port 8000.
2. Start frontend with npm run dev. Vite is configured to bind to 0.0.0.0.
3. From the other computer, open:
   - http://<linux-ip>:5173
4. Ensure backend CORS is set to that same frontend URL:
   - backend/.env -> FRONTEND_URL=http://<linux-ip>:5173
5. Optional explicit API override for frontend:
   - frontend/.env -> VITE_API_BASE_URL=http://<linux-ip>:8000/api/v1
6. Restart backend and frontend after changing .env files.

## Current Status

- Auth, budgets, categories, payment methods, expenses, and reporting endpoints are implemented.
- React frontend supports login/register and dashboard flows.
