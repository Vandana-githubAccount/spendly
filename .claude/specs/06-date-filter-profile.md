# Spec: Date Filter for Profile Page

## Overview
The profile page currently shows all-time summary stats, recent transactions, and category breakdown for the logged-in user with no way to narrow the view to a specific period. This feature adds a date-range filter to the profile page so users can scope those three sections (summary stats, recent transactions, category breakdown) to a preset window (last 7 days, last 30 days, this month) or a custom start/end date, using standard GET query parameters so the filtered view is shareable/bookmarkable and requires no new route.

## Depends on
- Step 4 (Profile page) — this feature modifies the existing `GET /profile` route and `profile.html` template built in that step.

## Routes
No new routes. The existing `GET /profile` route is modified to accept optional query parameters:
- `range` — one of `all`, `7d`, `30d`, `month`, `custom` (default: `all`)
- `start` — `YYYY-MM-DD`, required only when `range=custom`
- `end` — `YYYY-MM-DD`, required only when `range=custom`

Access level: logged-in (unchanged, still behind `login_required`).

## Database changes
No database changes. Filtering uses the existing `date` column (`TEXT`, `YYYY-MM-DD`) on `expenses`. Verified against `database/db.py` — no new tables/columns/constraints needed.

## Templates
- Create: none
- Modify:
  - `templates/profile.html` — add a date-filter control (range dropdown + conditional custom start/end date inputs) above the stats row, submitted via GET so the page reloads with query params. Reflect the currently active filter back into the control's selected value/inputs so it doesn't reset on reload. Show a friendly inline message when a custom range is invalid (start after end) instead of erroring.

## Files to change
- `app.py` — in the `profile` view: read `range`/`start`/`end` from `request.args`, validate them, resolve to a concrete `(start_date, end_date)` pair (or `None` for all-time), pass that through to the three query functions, and pass the resolved filter state back to the template so the UI reflects the current selection.
- `database/queries.py` — add optional `start_date`/`end_date` keyword arguments (default `None`) to `get_recent_transactions`, `get_summary_stats`, and `get_category_breakdown`. When both are provided, add a parameterized `AND date BETWEEN ? AND ?` clause to each existing query; when `None`, behavior is unchanged from today.
- `static/css/style.css` — add styles for the new filter control, using existing CSS variables only.
- `static/js/main.js` — add the minimal JS needed to show/hide the custom start/end date inputs when the range dropdown is set to "Custom range" (progressive enhancement only; the form still works via full-page GET submission without JS).

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug (unaffected by this feature, but preserved).
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- Invalid custom date input (malformed dates, or start after end) must never raise a server error — fall back to all-time and surface a friendly inline message instead.
- Date parsing/validation lives in `app.py`, not in the templates or the query layer.

## Definition of done
- Visiting `/profile` with no query params shows the same all-time stats, transactions, and category breakdown as before this change.
- Visiting `/profile?range=7d` shows stats/transactions/breakdown computed only from expenses dated within the last 7 days, and the filter control shows "Last 7 days" as selected.
- Visiting `/profile?range=30d` behaves the same way for a 30-day window.
- Visiting `/profile?range=month` filters to the current calendar month only.
- Selecting "Custom range" in the UI reveals start/end date inputs; submitting `/profile?range=custom&start=<date>&end=<date>` with a valid range filters all three sections to expenses within `[start, end]` inclusive, and the inputs retain the submitted values after reload.
- Submitting a custom range with `start` after `end`, or a malformed date, reloads `/profile` without a server error and shows a friendly inline validation message, falling back to all-time data.
- A filtered range with zero matching expenses shows `total_spent=0.00`, `transaction_count=0`, `top_category=—`, an empty transactions table, and an empty category breakdown — no exceptions.
- All new/changed SQL in `database/queries.py` uses parameterized placeholders (`?`), never string-formatted values.
