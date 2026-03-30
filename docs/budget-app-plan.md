## Plan: Budget App MVP Foundation

Build a learning-friendly full-stack budget app with FastAPI + SQLAlchemy backend, React frontend, and SQLite-first persistence designed for smooth migration to PostgreSQL later. Implement secure multi-account auth (email/password + Google), monthly budgeting with carry-forward behavior, expense tracking by category/payment method, and monthly/yearly analytics views, while keeping architecture modular and easy to understand.

**Steps**
1. Phase 1: Project setup and architecture decisions.
2. Define monorepo structure with separate backend and frontend apps plus shared docs for learning notes.
3. Backend stack setup: FastAPI app skeleton, SQLAlchemy 2.x ORM, Alembic migrations, Pydantic v2 schemas, and settings via environment variables. *blocks Phase 2*
4. Frontend stack setup: React + TypeScript + Vite, routing, API client layer, and auth state management. *parallel with backend domain modeling once API contracts are drafted*
5. Configure database abstraction for migration readiness: SQLite connection by default and PostgreSQL URL support through config only (no code rewrite target). *depends on Step 3*
6. Phase 2: Authentication and user accounts.
7. Implement user model and account lifecycle endpoints (register, login, refresh, profile).
8. Add password auth using passlib/bcrypt + JWT tokens.
9. Add Google OAuth login flow (Authlib + FastAPI callback endpoint) and map Google identity to local user account. *depends on user model*
10. Add frontend auth screens and protected route guard.
11. Phase 3: Budget and expense core features.
12. Implement budget entities supporting month-scoped budgets and recurring behavior as "copy previous month and allow edits."
13. Implement category model with default global categories plus user-defined categories.
14. Implement payment method model (cash, debit, credit, transfer, other) with extensibility.
15. Implement expense CRUD endpoints with required fields: category, description, payment method, amount, date.
16. Add recurring-expense templates (approved optional feature) with one-click create into current month.
17. Build frontend flows for creating budgets, adding expenses, and managing categories.
18. Phase 4: Reporting and analytics.
19. Build API aggregations for spend totals by category for selected month or year.
20. Build API and UI drill-down for one selected category across selected period.
21. Implement dashboard filters: month/year selector and category selector.
22. Phase 5: Quality, security, and developer ergonomics.
23. Add backend validation, error handling, and role-safe authorization checks per user account boundary.
24. Add automated tests for auth, budget recurrence, expense creation, and reporting queries.
25. Add frontend tests for core forms and analytics view behavior.
26. Add OpenAPI-based API docs and beginner-focused README walkthrough.

**Languages and libraries**
- Backend language: Python 3.12
- Frontend language: TypeScript (with React)
- Backend framework: FastAPI
- ORM/database toolkit: SQLAlchemy 2.x
- Migrations: Alembic
- Data validation: Pydantic v2
- Auth/security: python-jose (JWT), passlib[bcrypt], Authlib (Google OAuth), email-validator
- HTTP/server: Uvicorn
- SQLite driver: built-in sqlite3 via SQLAlchemy URL
- PostgreSQL driver for future migration: psycopg (v3)
- Frontend framework/build: React 18, Vite
- Frontend routing/state/data: React Router, TanStack Query (for API data sync)
- Forms/UI validation: React Hook Form + Zod
- HTTP client: Axios (or Fetch wrapper, pick one during implementation)
- Backend tests: pytest, httpx, pytest-asyncio
- Frontend tests: Vitest, React Testing Library
- Optional tooling: Ruff (lint), Black (format), mypy (type checking), ESLint + Prettier

**Relevant files**
- To be created during implementation after scaffold is initialized:
- backend application modules (config, models, schemas, routers, services, migrations, tests)
- frontend application modules (pages, components, api client, auth state, tests)
- root documentation and environment templates

**Verification**
1. Run backend test suite and ensure auth + domain logic pass.
2. Run frontend tests for forms and analytics filters.
3. Manually validate user journeys: register/login (email + Google), create month budget, copy previous month budget, add expense, view category totals by month/year, and category drill-down.
4. Switch DB URL from SQLite to PostgreSQL in config and run migrations on clean DB to verify migration readiness.
5. Review OpenAPI docs to ensure endpoints align with UI functionality.

**Decisions**
- Multiple accounts means independent users of the app, not shared budgets between accounts.
- Auth includes both email/password and Google login in v1.
- Budget recurrence behavior will be "copy previous month and allow edits."
- Categories will use defaults plus user custom categories.
- Approved optional feature: recurring-expense templates only.
- Explicitly excluded from v1: account-to-account collaborative budget sharing/invites.

**Further Considerations**
1. API versioning recommendation: start with /api/v1 to avoid breaking changes later.
2. Monetary precision recommendation: store amounts as Decimal/NUMERIC, never float.
3. Timezone recommendation: store timestamps in UTC and render local time in UI.
