# Food Redistribution Platform: notes for Claude Code

A church-ministry app that connects surplus food (restaurants, caterers,
families) with verified receiving organizations, using volunteers for
pickup and delivery. Built by Srilatha as a learning project; being
prepared for a small ministry pilot.

## How it is built

- `app.py`: the Streamlit website. Login first, then a sidebar menu per role.
- `app/backend.py`: the functions pages call (`*_from_api` names are kept
  from the old HTTP version). They call the services directly and return
  API-shaped data or `{"error": "..."}`.
- `app/*_service.py`: business rules and SQL (psycopg2, parameterized).
  Raise `ValueError` for rule failures users should see.
- `app/database.py`: pooled connections; `get_connection()` / `close()`.
- `app/schema.py`: `ensure_schema()` creates and updates tables, runs at
  app start, and must stay idempotent (only add, never drop).
- `app/auth.py` + `app/user_service.py`: Google login (`st.login`) and the
  `app_users` table with roles ADMIN, DONOR, ORGANIZATION, VOLUNTEER.
- `app/timeutil.py`: always use `now_local()` (India time), never
  `datetime.now()`. DB sessions also run in APP_TIMEZONE.
- `app/main.py`: optional FastAPI version with NO login; not deployed.

Hosting: Streamlit Community Cloud + Neon Postgres. Settings come from
env, `.env`, or Streamlit secrets (see `.streamlit/secrets.toml.example`).
Never put secrets in code; `.env` and `.streamlit/secrets.toml` are ignored.

## Run and test

```
pip install -r requirements-dev.txt
# .env for local use:
#   DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/food_redistribution
#   ADMIN_EMAILS=you@example.com
#   DEV_LOGIN=true
streamlit run app.py
```

Tests need a separate throw-away database because they empty every table:

```
$env:TEST_DATABASE_URL="postgresql://postgres:PASSWORD@localhost:5432/food_test"   # PowerShell
pytest
```

Run the full test suite before every commit. `tests/test_ui.py` clicks
through the real pages per role with Streamlit `AppTest`. Add a test for
each new rule or page.

## Conventions

- Keep changes small and reviewable; work on a branch and open a pull
  request for Srilatha to review. Explain changes in plain language: she
  is learning, and ministry volunteers are not technical.
- Each role must only see its own pages and data; contact details of
  others are for admins only. Check role gating whenever adding a page.
- Use `flash_success(...)` in app.py after an action so the page refreshes.

## Done

- Phase 1 (stabilize): no Render backend, Neon support, pooling, India
  time fix, clear errors, row locking, schema migration, clean
  requirements.
- Phase 2 (secure): Google login, roles, access requests, User Access page.

## Next (from the review report)

1. Deploy: Neon project, Google OAuth client, Streamlit secrets; move
   data off Render; retire the Render service.
2. Pilot with 1 admin, 2-3 donors, 1 organization, 3-5 volunteers.
3. Then only what the pilot asks for, likely: email notifications,
   delivery confirmation with meals served, monthly report for church
   leadership, edit/cancel donations, Telugu labels, mobile layout checks.
