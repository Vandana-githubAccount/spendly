# Spec: Add Expense

## Overview
Users can currently view their expenses on the profile page but have no way to record a new one — `/expenses/add` is a placeholder stub. This feature implements the add-expense form and the backend logic to insert a new expense row for the logged-in user, making the tracker actually usable for entering spending rather than only viewing seeded/sample data.

## Depends on
- Step 1 (Database Setup) — requires the `expenses` table created in `database/db.py`.
- Step 3 (Login and Logout) — requires `login_required` and an active session.
- Step 4 / Step 5 (Profile page + backend routes) — the new expense must show up in profile stats, recent transactions, and category breakdown, which read from the same `expenses` table.

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in
- `POST /expenses/add` — validate and insert a new expense for the current user, then redirect to `/profile` — logged-in

Both methods live on the existing `/expenses/add` route (replacing the current stub), following the same GET-renders/POST-processes pattern used by `/register` and `/login`.

## Database changes
No new tables or columns. The existing `expenses` table (`database/db.py`) already has every column needed: `user_id`, `amount`, `category`, `date`, `description`. Verified against `database/db.py` — no schema changes required, only a new insert helper function.

## Templates
- Create: `templates/add_expense.html` — form with fields for amount, category (select), date, and description, following the `auth-card` / `form-group` / `form-input` / `btn-submit` markup conventions already used in `register.html` and `profile.html`'s filter form. Shows an inline error banner (reusing the `.auth-error` class) when validation fails, with previously entered values preserved.
- Modify:
  - `templates/profile.html` — add an "Add expense" link/button (e.g. near the profile card or stats row) pointing to `url_for('add_expense')`, since there is currently no in-app way to reach the route.

## Files to change
- `app.py` — replace the `add_expense` stub with a GET/POST view: on GET render the empty form (date defaulted to today); on POST read `amount`, `category`, `date`, `description` from `request.form`, validate them, call the new `create_expense` helper, and redirect to `url_for('profile')` on success or re-render the form with an `error` and the submitted values on failure.
- `database/db.py` — add a `create_expense(user_id, amount, category, date, description)` function that runs a parameterized `INSERT INTO expenses (...) VALUES (?, ?, ?, ?, ?)` and returns the new row's id, following the same shape as the existing `create_user`.
- `templates/profile.html` — add the "Add expense" link/button described above.
- `static/css/style.css` — add any styling the new form needs beyond what `.auth-card`, `.form-group`, `.form-input`, and `.btn-submit` already provide (e.g. layout for the add-expense page section), using existing CSS variables only.

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug (unaffected by this feature, but preserved).
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- The category field must be a fixed dropdown limited to the 7 categories that already have CSS badge/bar styling defined in `static/css/style.css` (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`) — free-text categories would have no matching badge/bar color.
- Amount must be validated server-side as a positive number; invalid/zero/negative/non-numeric input must redisplay the form with a friendly inline error, never a server error (HTTP 500).
- Date must be validated server-side as a real `YYYY-MM-DD` date; invalid input must redisplay the form with a friendly inline error, never a server error.
- Description is optional and may be empty.
- Validation and parsing logic lives in `app.py`, not in the template or the database layer.

## Definition of done
- Visiting `/expenses/add` while logged out redirects to `/login`.
- Visiting `/expenses/add` while logged in shows a form with amount, category, date, and description fields, with date pre-filled to today.
- Submitting valid data (positive amount, valid category, valid date, with or without a description) creates a new row in `expenses` with the correct `user_id` and redirects to `/profile`.
- After a successful add, the new expense appears in "Recent transactions", and is reflected in the "Total spent"/"Top category" stats and the category breakdown on `/profile`.
- Submitting with a blank, zero, negative, or non-numeric amount redisplays the add-expense form with a friendly inline error and preserves the category/date/description the user already entered.
- Submitting with a missing or malformed date redisplays the add-expense form with a friendly inline error and preserves the other entered values.
- Submitting with an empty description succeeds and stores `NULL`/empty description.
- The add-expense form is reachable via a visible link/button from the profile page.
- All new SQL in `database/db.py` uses parameterized placeholders (`?`), never string-formatted values.
