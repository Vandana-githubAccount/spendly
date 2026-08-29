# Spec: Edit Expense

## Overview
Users can add expenses (Step 7) and view them on the profile page, but once an expense is recorded there is no way to correct a mistake — `/expenses/<id>/edit` is still a placeholder stub. This feature implements the edit-expense form and backend logic to update an existing expense row, reusing the same validation rules as add-expense while adding an ownership check so a user can only edit their own expenses.

## Depends on
- Step 1 (Database Setup) — requires the `expenses` table created in `database/db.py`.
- Step 3 (Login and Logout) — requires `login_required` and an active session.
- Step 4 / Step 5 (Profile page + backend routes) — the edit entry point lives on the "Recent transactions" table on `/profile`.
- Step 7 (Add Expense) — reuses the same field set (amount, category, date, description), validation rules, and form markup conventions established for `/expenses/add`.

## Routes
- `GET /expenses/<int:id>/edit` — render the edit-expense form pre-filled with the expense's current values — logged-in, owner-only
- `POST /expenses/<int:id>/edit` — validate and update the expense, then redirect to `/profile` — logged-in, owner-only

Both methods live on the existing `/expenses/<int:id>/edit` route (replacing the current stub), following the same GET-renders/POST-processes pattern used by `/expenses/add`. If the expense id doesn't exist or doesn't belong to the logged-in user, respond with a 404 rather than a server error.

## Database changes
No new tables or columns. The existing `expenses` table (`database/db.py`) already has every column needed. Verified against `database/db.py`:
- Add `get_expense_by_id(expense_id, user_id)` to `database/db.py` — parameterized `SELECT` scoped by **both** `id` and `user_id`, so a user can never fetch another user's expense by guessing an id. Returns `None` if not found or not owned.
- Add `update_expense(expense_id, user_id, amount, category, date, description)` to `database/db.py` — parameterized `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?`, following the same shape as the existing `create_expense`.
- Modify `get_recent_transactions` in `database/queries.py` to also `SELECT id` (currently selects only `date, description, category, amount`) — the profile page needs the expense id to build the edit link.

## Templates
- Create: `templates/edit_expense.html` — same `auth-card` / `form-group` / `form-input` / `btn-submit` markup as `templates/add_expense.html`, but fields are pre-filled with the expense's existing values and the form posts to `url_for('edit_expense', id=expense.id)`. Shows the same inline `.auth-error` banner on validation failure, preserving the user's submitted values.
- Modify:
  - `templates/profile.html` — add an "Edit" link per row in the "Recent transactions" table (e.g. a new "Actions" column), pointing to `url_for('edit_expense', id=tx.id)`.

## Files to change
- `app.py` — replace the `edit_expense` stub with a GET/POST view: look up the expense via `get_expense_by_id(id, session["user_id"])`, returning a 404 if `None`; on GET render the form pre-filled with the expense's current values; on POST read `amount`, `category`, `date`, `description` from `request.form`, validate them using the same rules as `add_expense` (reusing `VALID_CATEGORIES` and `DATE_FORMAT`), call `update_expense`, and redirect to `url_for('profile')` on success or re-render the form with an `error` and the submitted values on failure.
- `database/db.py` — add `get_expense_by_id` and `update_expense`.
- `database/queries.py` — add `id` to the `SELECT` in `get_recent_transactions`.
- `templates/profile.html` — add the "Edit" link described above.
- `templates/edit_expense.html` — new template (see Templates).

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug (unaffected by this feature, but preserved).
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- Every query and update in this feature must be scoped by `user_id` in addition to the expense `id` — never trust the `id` in the URL alone. A user requesting or submitting an id they don't own must get a 404, never another user's data and never a server error.
- The category field must be the same fixed dropdown of 7 categories used in `/expenses/add` (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`).
- Amount must be validated server-side as a positive number; invalid/zero/negative/non-numeric input must redisplay the form with a friendly inline error, never a server error (HTTP 500).
- Date must be validated server-side as a real `YYYY-MM-DD` date; invalid input must redisplay the form with a friendly inline error, never a server error.
- Description is optional and may be empty.
- Validation and parsing logic lives in `app.py`, not in the template or the database layer.

## Definition of done
- Visiting `/expenses/<id>/edit` while logged out redirects to `/login`.
- Visiting `/expenses/<id>/edit` for an expense that doesn't exist, or that belongs to a different user, returns a 404.
- Visiting `/expenses/<id>/edit` for an expense you own shows a form with amount, category, date, and description fields pre-filled with that expense's current values.
- Submitting valid changes (positive amount, valid category, valid date, with or without a description) updates the existing row in `expenses` (same `id`, same `user_id`) and redirects to `/profile`.
- After a successful edit, the updated values appear in "Recent transactions" and are reflected in the "Total spent"/"Top category" stats and the category breakdown on `/profile`.
- Submitting with a blank, zero, negative, or non-numeric amount redisplays the edit-expense form with a friendly inline error and preserves the category/date/description the user already entered.
- Submitting with a missing or malformed date redisplays the edit-expense form with a friendly inline error and preserves the other entered values.
- Submitting with an empty description succeeds and stores `NULL`/empty description.
- The edit form is reachable via a visible "Edit" link/button next to each transaction in the profile page's "Recent transactions" table.
- All new/modified SQL in `database/db.py` and `database/queries.py` uses parameterized placeholders (`?`), never string-formatted values.
