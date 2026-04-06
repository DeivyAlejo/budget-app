# Budget App

A full-stack personal budgeting app to plan monthly spending, track expenses, and visualize where money goes.

This is the first MVP version of the project.

## Features (MVP)

- User authentication
  - Register and login with email/password
- Monthly budgeting
  - Create monthly budget with planned allocations
  - Optional copy-from-previous-month behavior
  - Budget-by-category allocations
  - Budget vs income color indicator (red if budget exceeds income)
- Income tracking
  - Add, edit, and delete income entries
  - Income types: Salary, Freelance, Bonus, Other
  - Monthly income total
  - Income breakdown chart by type
  - Net balance calculation (Income - Expenses)
- Expense management
  - Add, edit, and delete expenses
  - Category and payment method assignment
  - Mark expenses as recurring
  - Track recurring vs one-time expenses
- Recurring expense automation
  - Create recurring expense templates
  - Auto-generate recurring expenses on monthly schedule
  - Dashboard reminders for upcoming recurring expenses
- Category and payment method management
  - Add and delete custom categories
  - Add and delete custom payment methods
- Reporting and dashboard
  - Month snapshot showing: Planned Budget, Total Income, Spent So Far, Net Balance
  - Category goals and drill-down detail view
  - Expenses table with recurring indicator
  - Income details table and income breakdown chart
  - Category totals and category detail drill-down
  - Donut expenses chart
- UX improvements
  - Collapsible management sections
  - Human-readable dates
  - Dashboard interactions that support quick editing
  - Color-coded alerts and indicators

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- SQLite (PostgreSQL-ready)

### Frontend

- React + TypeScript
- Vite
- TanStack Query
- Recharts

## Project Structure

- `backend/` FastAPI API, models, schemas, and tests
- `frontend/` React web app
- `docs/` planning and project docs

## Quick Start

## 1) Backend

```bash
cd backend
python -m venv .venv
```

Activate virtual environment:

- Linux/macOS:

```bash
source .venv/bin/activate
```

- Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and run API:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:

- API base URL: `http://localhost:8000/api/v1`
- Health check: `http://localhost:8000/api/v1/health`
- OpenAPI docs: `http://localhost:8000/docs`

## 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

## Environment Configuration

Use these files as templates:

- `backend/.env.example`
- `frontend/.env.example`

Important backend vars:

- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `FRONTEND_URL`
- `CORS_ORIGINS`

Optional frontend var:

- `VITE_API_BASE_URL`

## Access from Another Computer on LAN

1. Run backend with `--host 0.0.0.0 --port 8000`.
2. Run frontend with `npm run dev` (Vite is already configured for LAN access).
3. Open from another device: `http://<your-machine-ip>:5173`
4. Update backend CORS and frontend URL in `backend/.env`.
5. Optionally set `VITE_API_BASE_URL` in `frontend/.env`.
6. Restart backend and frontend after `.env` changes.

## Scripts

### Frontend

- `npm run dev` Start development server
- `npm run build` Build for production
- `npm run preview` Preview production build
- `npm run lint` Run lint checks

### Backend

- Run API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Run tests:

```bash
pytest
```

## Current MVP Status

Implemented and working:

- Auth, budgets, categories, payment methods, expenses, income, recurring expenses, and reporting endpoints
- Dashboard with:
  - Add expense form and expenses chart
  - Add income form and income breakdown chart
  - Category goals/detail panel
  - Expenses table with recurring indicator
  - Income details table
  - Month snapshot (Planned Budget, Total Income, Spent, Net Balance)
  - Color-coded budget vs income indicator
  - Management sections for categories and payment methods
  - Recurring expense reminders

## Roadmap Ideas

- Better chart label collision handling for large category sets
- Export/reporting options
- Recurring income templates (similar to recurring expenses)
- Income goals/targets per month
- Investment/savings tracking
- Optional PostgreSQL deployment profile

## License

No license file has been added yet.
