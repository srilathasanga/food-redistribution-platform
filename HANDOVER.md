# Handover: running the Food Redistribution app

For **Srilatha** (sangasrilatha8@gmail.com), the app owner from now on.
Pavan helped build the app and will step away after go-live. This page
explains what you own, what to do once, and what to do day to day.

Keep this page and the secret values safe. **Never paste passwords or
secrets into chat, email, GitHub or this file.** They belong only in
Streamlit → Settings → Secrets, and in your password manager.

---

## a. What you own

| What | What it does | Where to manage it |
|---|---|---|
| **GitHub repository** | The app's code. Streamlit takes the code from the `main` branch. | https://github.com/srilathasanga/food-redistribution-platform |
| **Streamlit app** | Runs the website people use. | https://share.streamlit.io (sign in with GitHub) |
| **Neon database** | Stores everything: people, kitchens, food, pickups. | https://console.neon.tech |
| **Google Cloud project** | The "Sign in with Google" button. | https://console.cloud.google.com/auth/overview |
| **Render** (old, to switch off) | The old version of the app. | https://dashboard.render.com |

The app's public privacy page is at
`https://YOUR-APP.streamlit.app/?page=privacy` (use your app's real address).

---

## b. Handover steps (do once, in this order)

**Before you start (with Pavan, while he still has access):** check that
*you* are the owner everywhere:
- GitHub: the repository is under your account (it is: `srilathasanga`).
- Streamlit: sign in at share.streamlit.io and check you can see the
  app and open **Settings**.
- Neon: the project shows up when *you* sign in to console.neon.tech.
- Google Cloud: you are listed with the **Owner** role under
  **IAM & Admin → IAM**.

If any of these is missing, ask Pavan to add you **before** step 5.

Do steps 2 and 3 together, in one sitting (about 20 minutes): between
them the app cannot reach the database or sign people in.

### 1. Google sign-in contact details
Google Cloud → **Google Auth Platform → Branding**
(https://console.cloud.google.com/auth/branding):
- **User support email**: `sangasrilatha8@gmail.com`
- **Developer contact information**: `sangasrilatha8@gmail.com`
- Click **Save**.

### 2. Make new secrets (Pavan had copies of the old ones)
Write each new value straight into your password manager.

1. **Database password**: Neon → your project → **Roles** →
   `neondb_owner` → **Reset password**. Then click **Connect**, choose the
   `main` branch, tick **Connection pooling**, and copy the connection
   string (it has `-pooler` in it). This is your new `DATABASE_URL`.
2. **Google client secret**: Google Cloud → **Google Auth Platform →
   Clients** (https://console.cloud.google.com/auth/clients) → your client
   → **Add secret**. Copy the new secret. *Do not delete the old one yet*
   (that comes after step 3, so sign-in keeps working).
3. **Cookie secret** (keeps people signed in): on your computer, open a
   terminal and run:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copy the long result.

### 3. Put the new secrets into Streamlit
share.streamlit.io → your app → **⋮ → Settings → Secrets**:
- `DATABASE_URL = "…the new pooled string from step 2.1…"`
- In the `[auth]` section: `client_secret = "…step 2.2…"` and
  `cookie_secret = "…step 2.3…"`
- `ADMIN_EMAILS = ["sangasrilatha8@gmail.com"]`
- Leave everything else as it is (`redirect_uri`, `client_id`, …).
  Never add `DEV_LOGIN`.

Click **Save**, then **⋮ → Reboot app**. Open the app and sign in.
Everyone will have to sign in again; that is expected.

When sign-in works: go back to Google Cloud → Clients → your client and
**disable, then delete, the old secret**.

### 4. Switch off Pavan's account in the app
In the app: **User access** → find Pavan → **Switch off access**.

### 5. Remove Pavan from the services
- **Neon**: project → **Settings → Collaborators** → remove Pavan.
- **Google Cloud**: **IAM & Admin → IAM**
  (https://console.cloud.google.com/iam-admin/iam) → Pavan → remove.
- **GitHub**: repository → **Settings → Collaborators** → remove Pavan.

### 6. Switch off Render
https://dashboard.render.com → the old web service → **Suspend** (later
**Delete**), and the same for the old Render database. The old version
has no sign-in, so it must not stay online.

### 7. Optional: make the code private
GitHub → repository → **Settings → Danger Zone → Change visibility →
Private**. If Streamlit then says it cannot read the repository, sign in
at share.streamlit.io and allow access to private repositories when it
asks.

---

## c. Everyday tasks

Sign in to the app. The **Home** page shows what needs you today, and
the menu shows small red numbers next to pages that need you.

- **Approve new people**: menu → **User access** → *Waiting for
  approval*. Check the name, phone and how they want to help. Change
  "Approve as" if needed, then **Approve** (or **Decline**). Anyone can
  sign in with Google, but nobody can use the app until you approve them.
- **Verify organizations**: menu → **Organizations** → *Waiting for
  verification*. Check that the home or shelter is real (call them if
  unsure), then **Verify**, or **Not approved** with a short reason they
  will see.
- **Pickups**: menu → **Pickup requests**:
  1. *To accept*: a home asked for food → **Accept**.
  2. *Needs a volunteer*: choose a free volunteer → **Assign volunteer**.
  3. *On the way*: the volunteer marks it picked up and delivered from
     their phone; you can also do it for them here.
- **Switch someone off** (they left, or misuse): **User access** → the
  person → **Switch off access**. You can switch them back on later.

---

## d. If something breaks

1. **Reboot first.** share.streamlit.io → the app → **⋮ → Reboot app**.
   This fixes most "stuck" problems.
2. **Read the logs.** Open the app, click **Manage app** (bottom-right
   corner). A panel opens with the latest messages; errors are in red.
   Copy them (never copy secrets) into Claude Code and ask what they mean.
3. **"We can't reach the app's database right now"**: this friendly
   screen means the app is fine but cannot reach Neon. Usually:
   - Neon is briefly down or waking up: wait a minute, click **Try again**.
   - The password or `DATABASE_URL` in Streamlit Secrets is wrong (for
     example after a password reset): copy the pooled string from Neon
     again, paste it into Secrets, Save, Reboot.
   - The free Neon plan ran out of its monthly allowance: check the
     Neon console for a warning.
   People's information is safe; nothing is lost.
4. **Roll back a bad change to the code.** The database is never changed
   by a rollback (the app only ever adds tables or columns).
   - Once, right after go-live, mark the working version with a tag. In
     VS Code's terminal, in the project folder:
     ```
     git switch main
     git pull
     git tag go-live
     git push origin go-live
     ```
   - To go back to that version later, without deleting any history:
     ```
     git switch main
     git pull
     git revert --no-commit go-live..HEAD
     git commit -m "Roll back to the go-live version"
     git push
     ```
     Streamlit redeploys within a few minutes.
   - The older tag `backup-before-changes-2026-11-16` is from **before**
     Google sign-in existed. Do **not** roll back to it: the app would
     have no sign-in.
5. **Database mistakes** (for example something deleted by accident):
   Neon → your project → **Restore** can bring the database back to a
   recent time (the free plan keeps only a short history), or use your
   latest monthly backup (below). Ask for help before restoring.

---

## e. Monthly backup (about 10 minutes, first week of each month)

You need the PostgreSQL command-line tools once: download the Windows
installer from https://www.postgresql.org/download/windows/, and in the
installer tick only **Command Line Tools**. Use the same or a newer
version than your Neon database (Neon shows it on the project page).

1. Neon → your project → **Connect** → branch `main` → **untick**
   *Connection pooling* → copy the connection string (no `-pooler`).
2. Open PowerShell in a folder you choose and run (paste your string
   between the quotes, and change the date):
   ```
   pg_dump --no-owner --no-acl "postgresql://neondb_owner:PASSWORD@ep-xxxx.REGION.aws.neon.tech/neondb?sslmode=require" -f food-backup-2026-12.sql
   ```
   (If `pg_dump` is "not recognized", use its full path, for example
   `& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" …`.)
3. Check the file is not empty (a few hundred KB or more is normal).
4. Upload it to a **private** Google Drive folder (for example
   *Ministry → App backups*). Do not share the folder: the file contains
   names, phone numbers and addresses.
5. Delete the copy on your computer, and close PowerShell so the
   password is not left on screen. Keep the last 12 backups in Drive.

To restore a backup, ask for help: it should go into a **new Neon
branch** first, never straight over the live database.

---

## f. Making changes later

1. Open the project folder in **VS Code** and start **Claude Code**. The
   file `CLAUDE.md` tells Claude how the app is built and the safety
   rules, so you can ask in plain words ("add a phone number to the
   volunteer card").
2. Work on a branch, not `main`. Try it on your computer:
   `streamlit run app.py`. Careful: if your computer has
   `.streamlit/secrets.toml` with the **real** database, this uses real
   data (see README). For safe testing use a Neon test branch.
3. Run the tests: `python -m pytest` (see README "Testing"; they need a
   separate test database and empty it).
4. Commit and push, then merge into `main` on GitHub. Streamlit redeploys
   automatically within a few minutes. Open the app and check.

Useful files: `README.md` (setup and go-live details), `CLAUDE.md`
(how the code is organised), `app/privacy.py` (ministry name and the
privacy contact).
