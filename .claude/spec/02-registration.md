# Spec: Registration

## Overview

Implements account creation for Spendly. The `/register` route currently only
renders `templates/register.html` on GET; this step adds the POST handler
that validates the submitted form, hashes the password, and inserts a new
row into the `users` table. This is the second step in the roadmap and turns
the static registration page (already built) into a working feature backed
by the database layer from Step 1. Logging the new user in automatically is
out of scope — session handling arrives in Step 3 (Login/Logout), so a
successful registration redirects to `/login`.

## Depends on

- Step 1 (Database Setup) — requires `get_db()` and the `users` table
  (`name`, `email`, `password_hash`, `created_at`) to already exist.

## Routes

- POST /register - validate the submitted name/email/password, create the user, redirect to /login on success - public
- GET /register - unchanged, still renders the registration form - public

## Database changes

No database changes. The existing `users` table (`id`, `name`, `email`
UNIQUE, `password_hash`, `created_at`) already supports registration —
verified against `database/db.py`.

## Templates

- Create: none
- Modify: none — `templates/register.html` already extends `base.html`,
  posts to `/register`, and renders `{% if error %}` for validation
  messages. No template changes are required.

## Files to change

- `app.py` — change the `/register` route to accept `GET` and `POST`. On
  POST: read `name`, `email`, `password` from the form, validate them,
  check for a duplicate email, hash the password with werkzeug, insert the
  user, then redirect to `/login`. On validation failure, re-render
  `register.html` with an `error` message and the submitted `name`/`email`
  values.
- `database/db.py` — add `get_user_by_email(email)` and `create_user(name,
  email, password_hash)` helper functions using the same `get_db()`
  connection pattern as `seed_db()`.

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend base.html
- Validate server-side: `name` and `email` non-empty, `email` contains
  `@`, `password` at least 8 characters (matches the field's placeholder
  text)
- Check `get_user_by_email()` before inserting; also handle
  `sqlite3.IntegrityError` from the `UNIQUE` constraint as a fallback
- Never store or log the plaintext password

## Definition of done

- [ ] Submitting the register form with valid, unique data creates a new
      row in `users` with a bcrypt/werkzeug password hash (not plaintext)
- [ ] Submitting with an email that already exists re-renders the form
      with an error and does not create a duplicate row
- [ ] Submitting with a password under 8 characters re-renders the form
      with an error and does not create a user
- [ ] After a successful registration, the browser is redirected to
      `/login`
- [ ] GET /register still renders the form with no errors
- [ ] Restarting the app does not duplicate or affect existing users
