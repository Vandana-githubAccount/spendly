# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

This is a guided, step-by-step learning project: a Flask expense tracker built incrementally as a course. Routes and files are deliberately left as stubs until the corresponding step is reached — don't "complete" a stub ahead of what's being worked on unless asked. Current stub markers to be aware of:

- `database/db.py` — Step 1 (Database Setup). Should eventually contain `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample dev data). Currently empty except for the spec comment.
- `static/js/main.js` — placeholder, JS is added as features are built.
- `app.py` placeholder routes returning plain-text stubs: `/logout` (Step 3), `/profile` (Step 4), `/expenses/add` (Step 7), `/expenses/<id>/edit` (Step 8), `/expenses/<id>/delete` (Step 9).

## Commands

Activate the venv before running Python commands (PowerShell):
```
venv\Scripts\Activate.ps1
```

Install dependencies:
```
pip install -r requirements.txt
```

Run the dev server (port 5001, debug mode):
```
python app.py
```

Run tests (pytest + pytest-flask are in requirements.txt; no test files exist yet — add them under a `tests/` directory using the `client` fixture from pytest-flask):
```
pytest
```

## Architecture

- **`app.py`** is the single Flask entry point — all routes are defined directly on the `app` object here (no blueprints). New routes should follow the same flat pattern unless the project grows enough to warrant blueprints.
- **Templates** (`templates/`) use Jinja2 inheritance from `base.html`, which defines the page shell (nav, footer, font/CSS links) and exposes `{% block title %}`, `{% block head %}`, `{% block content %}`, and `{% block scripts %}` for child templates to override. Every new page template should extend `base.html` and only fill in these blocks.
- **Static assets** live under `static/css/style.css` and `static/js/main.js`, referenced via `url_for('static', filename=...)` — keep new CSS/JS in these same files unless a page needs something clearly page-specific.
- **Database** (`database/`) will hold the SQLite access layer once Step 1 is implemented. The DB file itself (`expense_tracker.db`) is gitignored and created at runtime via `init_db()`/`seed_db()`, not committed.
- Branding: the app/site name in templates is "Spendly".
