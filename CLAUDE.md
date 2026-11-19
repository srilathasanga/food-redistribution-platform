# Food Redistribution Platform: notes for Claude Code

A church-ministry app that connects surplus food (restaurants, caterers,
families) with verified receiving organizations, using volunteers for
pickup and delivery. Built by Srilatha as a learning project; being
prepared for a small ministry pilot.

## How it is built

- `app.py`: set-up, sign-in and the menu only (small). Order: page config
  → `ui.apply_style()` → public privacy page (`?page=privacy`, before
  login and database) → `prepare_database()` (friendly screen if it
  fails) → `require_user()` → `st.navigation` menu.
- `app/navigation.py`: which role sees which page (one list). A page not
  in a role's list cannot be opened; `only_for_this_role` in app.py
  double-checks. Update it, and `tests/test_navigation.py`, for every
  new page.
- `app/screens/*.py`: one file per group of pages; each page function
  takes a `PageContext` (`ctx.user`, `ctx.role`, `ctx.is_admin`,
  `ctx.my_restaurant`, `ctx.my_organization`, `ctx.pages` for links).
  `app/home_pages.py`: the Home page per role, plus shared cards (food
  card + request pop-up, pickup line, volunteer card).
- `app/ui.py`: the shared look: `page_header`, `card`, `stat_card` /
  `stat_row` (4 in a row, 2x2 on phones), `checklist`, `quick_actions`
  (+ `form_requested`: the target page opens that form),
  `grid` (row by row, keeps order on phones), `badge_markdown` /
  `pickup_status`, `empty_state`, `status_chart`, `friendly_time`,
  `flash_success`, `rows`, `amount`, `plural`. ALL custom CSS lives here.
  Colours, fonts and sizes live in `.streamlit/config.toml`.
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
- `app/privacy.py`: public privacy policy; `MINISTRY_NAME` is defined here.
- `app/config.py`: settings; environment values present at start-up win
  over `secrets.toml` (protects the tests, see below).
- `app/timeutil.py`: always use `now_local()` (India time), never
  `datetime.now()`. DB sessions also run in APP_TIMEZONE.
- `app/main.py`: optional FastAPI version with NO login; not deployed.

Hosting: Streamlit Community Cloud + Neon Postgres. Settings come from
env, `.env`, or Streamlit secrets (see `.streamlit/secrets.toml.example`).
Never put secrets in code; `.env`, `.streamlit/secrets.toml` and the
personal notes file `Info-Food-Dist-App.txt` are git-ignored. Never print
or commit secrets.

- Privacy policy URL (for Google Auth Platform → Branding):
  `https://YOUR-APP.streamlit.app/?page=privacy`
- Google sign-in is in **Testing** mode: each new person must first be
  added in Google Cloud → Google Auth Platform → Audience → Test users,
  then sign in and ask for access, then an admin approves them.
- `redirect_uri` must end in `/oauth2callback` (live address in the
  Streamlit Cloud secrets; localhost in the local file).

## Run and test

```
pip install -r requirements-dev.txt
# .env for local use:
#   DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/food_redistribution
#   ADMIN_EMAILS=you@example.com
#   DEV_LOGIN=true
streamlit run app.py
```

WARNING: on the development laptop `.streamlit/secrets.toml` points
at the PRODUCTION Neon database, and under `streamlit run` secrets.toml
wins over `.env` and environment variables. So `streamlit run app.py`
there uses real data. To check pages without a database, use
`streamlit run dev/ui_preview.py`, or render pages with `AppTest` in a
copy of the project WITHOUT secrets.toml. Never run SQL that deletes,
truncates or drops data on that database.

Tests need a separate throw-away database because they empty every table
(a local Postgres database or a Neon test-only branch):

```
$env:TEST_DATABASE_URL="postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"   # PowerShell, same terminal
python -m pytest   # "pytest" alone may be blocked by Windows Application Control
```

TEST SAFETY (do not weaken): Streamlit copies secrets.toml over
DATABASE_URL the first time a secret is read, which once meant pytest
could empty the real database. Now (1) `app/config.py` keeps start-up
environment values, and (2) `tests/conftest.py` + `tests/db_safety.py`
check the LIVE connection's host and database name before anything is
created or emptied: it must match TEST_DATABASE_URL and must not match
the database in secrets.toml (Neon `-pooler` hosts count as the same);
otherwise the whole run stops. `tests/test_settings_safety.py` proves it.
Tests marked `@pytest.mark.no_database` run without any database.

Run the full test suite before every commit (it takes about 20 minutes
against Neon). `tests/test_ui.py` clicks through the real pages per role
with Streamlit `AppTest` (open a page with `go_to(at, "url-path")`).
After a click that saves something (flash_success -> st.rerun), open the
next page with a fresh `open_app(...)`: AppTest keeps stale elements
after a rerun, a real browser does not. Add a test for each new rule or
page.

## Conventions

- Keep changes small and reviewable; work on a branch and open a pull
  request for Srilatha to review. Explain changes in plain language: she
  is learning, and ministry volunteers are not technical.
- Each role must only see its own pages and data; contact details of
  others are for admins only. Exception: a volunteer sees the delivery
  address and contact for their OWN ACTIVE pickups only, enforced in SQL
  (`get_volunteer_pickups`). Check role gating whenever adding a page.
- After an action call `ui.flash_success("What happened. Next: ...")`
  so the page refreshes and people know the next step.
- Pages: start with `ui.page_header(title, one-line purpose, icon)`; show
  lists as cards (`ui.card`, `ui.grid`) with `ui.badge_markdown` status
  badges (words + icon, never colour alone); use `ui.empty_state` for
  empty lists; plain words, no raw IDs or status codes.
- Colour balance: only ONE strong gradient block per page (the Home
  impact strip, shown once the first delivery is done; before that the
  admin sees a light "Getting started" checklist). Banners, cards and
  stat cards stay light; colour comes from icons, badges and stripes.
  The sidebar is the only dark area.
- Design is FROZEN for go-live (2026-11-19): fix bugs and contrast only;
  new visual ideas wait until after the pilot.
- Accessibility: every text/background pair WCAG AA (4.5:1); coral is
  never behind white text; nothing under 15px; tap targets >= 24px
  (aim for 40px+). Check at 390px wide: no sideways scrolling.

## Done

- Phase 1 (stabilize): no Render backend, Neon support, pooling, India
  time fix, clear errors, row locking, schema migration, clean
  requirements.
- Phase 2 (secure): Google login, roles, access requests, User access page,
  public privacy page, friendly database-error screen, test-safety guard.
- Phase 3 (design): royal blue + coral theme, role home pages, menu with
  st.navigation, friendly sign-in, forms and card lists, admin pages
  grouped by next action, Volunteers page, phone and accessibility pass;
  warmer look (illustrations, avatars, pickup tracker), dark navy
  sidebar with count badges, light banners, admin Home quick actions.

## Next

1. Before go-live: run the full suite against the Neon test-only branch
   and fix failures.
2. Move the form-only checks into the services (with tests): organization
   address required; food quantity and pickup address required; phone
   (10-digit mobile) and email format; food cannot be posted already
   expired. Today only the Streamlit forms enforce them.
3. Go-live checklist (details in README): (1) owner saves Streamlit
   Secrets, (2) clear test data in Neon SQL Editor (after a
   `before-go-live` branch), (3) merge stabilize-and-secure into main and
   push, (4) sign in and check, (5) suspend Render.
4. Pilot with 1 admin, 2-3 donors, 1 organization, 3-5 volunteers.
5. Then only what the pilot asks for, likely: email notifications,
   delivery confirmation with meals served, monthly report for church
   leadership, edit/cancel donations, Telugu labels, more than one active
   pickup per volunteer.
