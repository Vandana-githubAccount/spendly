# Spec: Login and Logout

## Overview

Implements session-based authentication for Spendly: a working `/login`
that verifies credentials created by Step 2 (Registration) and starts a
session, and a `/logout` that ends it. This is the third step in the
roadmap and is the first place the app distinguishes a logged-in visitor
from an anonymous one. Since the remaining placeholder routes (`/profile`,
`/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) are meant
to be personal, logged-in-only pages, this step also introduces a
`login_required` guard and applies it to them — their bodies stay the
existing stub text ("coming in Step N"), only the access gate is added, so
later steps can fill them in without touching auth again.

## Depends on

- Step 1 (Database Setup) — `get_db()` and the `users` table.
- Step 2 (Registration) — `get_user_by_email()` and the fact that
  `users.password_hash` is a werkzeug hash, needed to verify login
  credentials.

## Routes

No new routes. Two existing stub routes gain real behavior, and four
existing stub routes gain an auth gate:

- POST /login - verify email/password, start a session, redirect to /profile - public
- GET /login - unchanged, still renders the login form - public
- GET /logout - clear the session, redirect to /login - logged-in
- GET /profile - unchanged stub body, now redirects to /login if not authenticated - logged-in
- GET /expenses/add - unchanged stub body, now redirects to /login if not authenticated - logged-in
- GET /expenses/<id>/edit - unchanged stub body, now redirects to /login if not authenticated - logged-in
- GET /expenses/<id>/delete - unchanged stub body, now redirects to /login if not authenticated - logged-in

## Database changes

No database changes. Login only needs to read the existing `users` table
via `get_user_by_email()` (added in Step 2) — verified against
`database/db.py`.

## Templates

- Create: none
- Modify:
    - `templates/login.html` — add `value="{{ email or '' }}"` to the
      email input so it round-trips on a failed login, matching the
      pattern already used in `templates/register.html`. Password input
      is left blank, same as registration.
    - `templates/base.html` — the nav currently always shows "Sign in" /
      "Get started". Change it to check `session.user_id`: when logged
      out, show the existing links; when logged in, show a link to
      `/profile` and a link to `/logout` instead, reusing the existing
      `nav-links` / `nav-cta` CSS classes (no new CSS needed).

## Files to change

- `app.py`:
    - Set `app.config["SECRET_KEY"]` (required for Flask's signed session
      cookies to work at all).
    - Import `session`, `check_password_hash`, and `functools.wraps`.
    - Implement `POST /login`: look up the user by (lowercased, stripped)
      email, verify the password with `check_password_hash`, and on
      success store only `session["user_id"] = user["id"]` and redirect
      to `/profile`. On any failure (no such user, or wrong password),
      re-render `login.html` with one generic error — never reveal
      whether the email or the password was the problem.
    - Implement `GET /logout`: `session.clear()`, redirect to `/login`.
    - Add a `login_required` decorator that checks `session.get("user_id")`
      and redirects to `/login` if it's missing, otherwise calls the
      wrapped view.
    - Apply `@login_required` to `profile`, `add_expense`, `edit_expense`,
      `delete_expense` — their bodies stay exactly as they are today.
- `database/db.py` — no changes.

## Files to create

None.

## New dependencies

No new dependencies. `check_password_hash` is part of `werkzeug.security`,
already installed.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend base.html
- Verify passwords with `werkzeug.security.check_password_hash` —
  never compare plaintext passwords
- Store only `user_id` in the session — never the password or password
  hash
- Use one generic error message ("Invalid email or password.") for both
  "no such user" and "wrong password", so login can't be used to
  enumerate registered emails
- Normalize email the same way as registration (`.strip().lower()`)
  before calling `get_user_by_email()`
- `login_required` must not change the stub response bodies of the
  routes it guards — it only adds the redirect-if-unauthenticated check

## Definition of done

- [ ] Logging in with the seeded demo account (`demo@spendly.com` /
      `demo123`) or a freshly registered account succeeds and redirects
      to `/profile`
- [ ] Logging in with a correct email but wrong password re-renders
      `login.html` with a generic "Invalid email or password." error and
      does not set a session
- [ ] Logging in with an email that doesn't exist shows the exact same
      generic error message as a wrong password
- [ ] Visiting `/profile` directly in a fresh (logged-out) browser
      session redirects to `/login`
- [ ] Visiting `/expenses/add`, `/expenses/<id>/edit`, or
      `/expenses/<id>/delete` while logged out redirects to `/login`
- [ ] After logging in, visiting `/profile` no longer redirects and shows
      the existing stub text
- [ ] Clicking the logout link clears the session; visiting `/profile`
      afterward redirects to `/login` again
- [ ] The navbar shows "Sign in" / "Get started" when logged out, and a
      "Profile" / "Logout" link when logged in
