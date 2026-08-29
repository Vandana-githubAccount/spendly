"""Tests for the Add Expense feature.

Spec: .claude/specs/07-add-expense.md

Covers:
- Auth guard: GET/POST /expenses/add redirect to /login when logged out.
- GET renders the add-expense form with amount/category/date/description
  fields, the fixed 7-category dropdown, and the date pre-filled to today.
- Successful POST creates a row in `expenses` with the correct user_id and
  redirects to /profile.
- Validation: blank/zero/negative/non-numeric amount, invalid category, and
  blank/malformed date all redisplay the form with a friendly inline error
  (never a 500) and preserve the other submitted values.
- Empty description is optional and succeeds.
- Definition-of-done: a successfully added expense is reflected on /profile
  (recent transactions, total spent, category breakdown), and the
  add-expense page is reachable via a link from /profile.

These tests are black-box / spec-driven: they exercise the app only through
the Flask test client and verify outcomes via HTTP responses and direct,
parameterized reads of the `expenses` table.
"""

from datetime import date

import pytest

from database.db import get_db

DEMO_USER_ID = 1

ADD_EXPENSE_URL = "/expenses/add"
PROFILE_URL = "/profile"
LOGIN_URL = "/login"

VALID_CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]

VALID_FORM = {
    "amount": "25.50",
    "category": "Food",
    "date": "2026-01-15",
    "description": "Groceries",
}


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def login(client, user_id=DEMO_USER_ID):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def valid_form(**overrides):
    data = dict(VALID_FORM)
    data.update(overrides)
    return data


def total_expense_count():
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) AS c FROM expenses").fetchone()
    conn.close()
    return row["c"]


def expense_count_for_user(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["c"]


def latest_expense_for_user(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


def assert_no_server_error(response):
    assert response.status_code < 500, "Invalid input must never cause a server error"
    body = response.get_data(as_text=True)
    assert "Traceback" not in body, "Response should not leak a traceback"
    assert "Internal Server Error" not in body


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

class TestAddExpenseAuthGuard:
    def test_get_redirects_when_logged_out(self, client):
        response = client.get(ADD_EXPENSE_URL)
        assert response.status_code == 302, "Unauthenticated GET should redirect"
        assert LOGIN_URL in response.headers["Location"], "Should redirect to login"

    def test_post_redirects_when_logged_out(self, client):
        response = client.post(ADD_EXPENSE_URL, data=valid_form())
        assert response.status_code == 302, "Unauthenticated POST should redirect"
        assert LOGIN_URL in response.headers["Location"], "Should redirect to login"

    def test_post_while_logged_out_does_not_create_an_expense(self, client):
        before = total_expense_count()
        client.post(ADD_EXPENSE_URL, data=valid_form())
        after = total_expense_count()
        assert after == before, "No expense should be created for an unauthenticated request"


# ------------------------------------------------------------------ #
# GET renders the form                                                #
# ------------------------------------------------------------------ #

class TestAddExpenseFormRendering:
    def test_get_returns_200_when_logged_in(self, client):
        login(client)
        response = client.get(ADD_EXPENSE_URL)
        assert response.status_code == 200

    def test_get_renders_expected_form_fields(self, client):
        login(client)
        response = client.get(ADD_EXPENSE_URL)
        body = response.get_data(as_text=True)
        assert 'name="amount"' in body, "Form should have an amount field"
        assert 'name="category"' in body, "Form should have a category field"
        assert 'name="date"' in body, "Form should have a date field"
        assert 'name="description"' in body, "Form should have a description field"

    def test_get_form_posts_to_add_expense_route(self, client):
        login(client)
        response = client.get(ADD_EXPENSE_URL)
        body = response.get_data(as_text=True)
        assert f'action="{ADD_EXPENSE_URL}"' in body, "Form should submit back to /expenses/add"

    @pytest.mark.parametrize("category", VALID_CATEGORIES)
    def test_get_category_dropdown_includes_each_valid_category(self, client, category):
        login(client)
        response = client.get(ADD_EXPENSE_URL)
        body = response.get_data(as_text=True)
        assert f'value="{category}"' in body, f"{category} should be an option in the category dropdown"

    def test_get_date_defaults_to_today(self, client):
        login(client)
        response = client.get(ADD_EXPENSE_URL)
        body = response.get_data(as_text=True)
        today_iso = date.today().isoformat()
        assert f'value="{today_iso}"' in body, "Date field should default to today's date"


# ------------------------------------------------------------------ #
# Successful submission                                               #
# ------------------------------------------------------------------ #

class TestAddExpenseSuccess:
    def test_valid_submission_redirects_to_profile(self, client):
        login(client)
        response = client.post(ADD_EXPENSE_URL, data=valid_form())
        assert response.status_code == 302, "Successful submission should redirect"
        assert PROFILE_URL in response.headers["Location"], "Should redirect to /profile"

    def test_valid_submission_creates_row_with_correct_fields(self, client):
        login(client)
        client.post(
            ADD_EXPENSE_URL,
            data=valid_form(amount="99.95", category="Shopping", date="2026-02-10", description="New shoes"),
        )
        row = latest_expense_for_user(DEMO_USER_ID)
        assert row is not None, "A new expense row should have been created"
        assert row["user_id"] == DEMO_USER_ID
        assert row["amount"] == pytest.approx(99.95)
        assert row["category"] == "Shopping"
        assert row["date"] == "2026-02-10"
        assert row["description"] == "New shoes"

    def test_valid_submission_increases_users_expense_count_by_one(self, client):
        login(client)
        before = expense_count_for_user(DEMO_USER_ID)
        client.post(ADD_EXPENSE_URL, data=valid_form())
        after = expense_count_for_user(DEMO_USER_ID)
        assert after == before + 1, "Exactly one new expense should be created"

    def test_valid_submission_with_empty_description_succeeds(self, client):
        login(client)
        response = client.post(ADD_EXPENSE_URL, data=valid_form(description=""))
        assert response.status_code == 302, "Empty description must not be a validation error"
        assert PROFILE_URL in response.headers["Location"]

    def test_valid_submission_with_empty_description_stores_empty_or_null(self, client):
        login(client)
        client.post(ADD_EXPENSE_URL, data=valid_form(description="", date="2026-03-03", amount="12.34"))
        row = latest_expense_for_user(DEMO_USER_ID)
        assert row is not None
        assert row["description"] in (None, ""), "Empty description should be stored as NULL or empty"

    def test_valid_submission_without_description_field_at_all_succeeds(self, client):
        login(client)
        data = valid_form()
        del data["description"]
        response = client.post(ADD_EXPENSE_URL, data=data)
        assert response.status_code == 302, "A missing description field should be treated as optional"

    def test_valid_submission_integer_amount_succeeds(self, client):
        login(client)
        response = client.post(ADD_EXPENSE_URL, data=valid_form(amount="10"))
        assert response.status_code == 302, "A whole-number amount should be accepted"

    def test_valid_submission_preserves_sql_injection_attempt_as_literal_text(self, client):
        login(client)
        malicious_description = "'); DROP TABLE expenses; --"
        response = client.post(ADD_EXPENSE_URL, data=valid_form(description=malicious_description))
        assert response.status_code == 302, "A crafted description should be treated as plain text, not SQL"
        row = latest_expense_for_user(DEMO_USER_ID)
        assert row["description"] == malicious_description
        # The table must still exist and contain all prior rows.
        assert total_expense_count() >= 1


# ------------------------------------------------------------------ #
# Amount validation                                                   #
# ------------------------------------------------------------------ #

class TestAddExpenseAmountValidation:
    @pytest.mark.parametrize(
        "bad_amount",
        ["", "0", "0.00", "-5", "-0.01", "abc", "12.5.6", "twenty"],
    )
    def test_invalid_amount_redisplays_form_with_error(self, client, bad_amount):
        login(client)
        response = client.post(ADD_EXPENSE_URL, data=valid_form(amount=bad_amount))
        assert_no_server_error(response)
        assert response.status_code == 200, "Invalid amount should redisplay the form, not redirect"
        body = response.get_data(as_text=True)
        assert "auth-error" in body, "A friendly inline error should be shown"

    @pytest.mark.parametrize(
        "bad_amount",
        ["", "0", "-5", "abc"],
    )
    def test_invalid_amount_preserves_other_submitted_values(self, client, bad_amount):
        login(client)
        response = client.post(
            ADD_EXPENSE_URL,
            data=valid_form(amount=bad_amount, category="Health", date="2026-04-04", description="Checkup"),
        )
        body = response.get_data(as_text=True)
        assert 'value="Health" selected' in body, "Category should be preserved"
        assert 'value="2026-04-04"' in body, "Date should be preserved"
        assert 'value="Checkup"' in body, "Description should be preserved"

    @pytest.mark.parametrize("bad_amount", ["", "0", "-5", "abc"])
    def test_invalid_amount_does_not_create_a_row(self, client, bad_amount):
        login(client)
        before = expense_count_for_user(DEMO_USER_ID)
        client.post(ADD_EXPENSE_URL, data=valid_form(amount=bad_amount))
        after = expense_count_for_user(DEMO_USER_ID)
        assert after == before, "No row should be created when the amount is invalid"


# ------------------------------------------------------------------ #
# Category validation                                                 #
# ------------------------------------------------------------------ #

class TestAddExpenseCategoryValidation:
    @pytest.mark.parametrize(
        "bad_category",
        ["NotACategory", "", "food", "Groceries", "<script>alert(1)</script>"],
    )
    def test_invalid_category_redisplays_form_with_error(self, client, bad_category):
        login(client)
        response = client.post(ADD_EXPENSE_URL, data=valid_form(category=bad_category))
        assert_no_server_error(response)
        assert response.status_code == 200, "Invalid category should redisplay the form, not redirect"
        body = response.get_data(as_text=True)
        assert "auth-error" in body, "A friendly inline error should be shown"

    def test_invalid_category_preserves_other_submitted_values(self, client):
        login(client)
        response = client.post(
            ADD_EXPENSE_URL,
            data=valid_form(category="NotACategory", amount="42.00", date="2026-05-05", description="Odd item"),
        )
        body = response.get_data(as_text=True)
        assert 'value="42' in body, "Amount should be preserved"
        assert 'value="2026-05-05"' in body, "Date should be preserved"
        assert 'value="Odd item"' in body, "Description should be preserved"

    @pytest.mark.parametrize("bad_category", ["NotACategory", "", "food"])
    def test_invalid_category_does_not_create_a_row(self, client, bad_category):
        login(client)
        before = expense_count_for_user(DEMO_USER_ID)
        client.post(ADD_EXPENSE_URL, data=valid_form(category=bad_category))
        after = expense_count_for_user(DEMO_USER_ID)
        assert after == before, "No row should be created when the category is invalid"


# ------------------------------------------------------------------ #
# Date validation                                                     #
# ------------------------------------------------------------------ #

class TestAddExpenseDateValidation:
    @pytest.mark.parametrize(
        "bad_date",
        ["", "not-a-date", "2026-13-40", "31/01/2026", "2026/01/31", "2026-02-30"],
    )
    def test_invalid_date_redisplays_form_with_error(self, client, bad_date):
        login(client)
        response = client.post(ADD_EXPENSE_URL, data=valid_form(date=bad_date))
        assert_no_server_error(response)
        assert response.status_code == 200, "Invalid date should redisplay the form, not redirect"
        body = response.get_data(as_text=True)
        assert "auth-error" in body, "A friendly inline error should be shown"

    def test_invalid_date_preserves_other_submitted_values(self, client):
        login(client)
        response = client.post(
            ADD_EXPENSE_URL,
            data=valid_form(date="not-a-date", amount="17.00", category="Entertainment", description="Concert"),
        )
        body = response.get_data(as_text=True)
        assert 'value="17' in body, "Amount should be preserved"
        assert 'value="Entertainment" selected' in body, "Category should be preserved"
        assert 'value="Concert"' in body, "Description should be preserved"

    @pytest.mark.parametrize("bad_date", ["", "not-a-date", "2026-13-40", "31/01/2026"])
    def test_invalid_date_does_not_create_a_row(self, client, bad_date):
        login(client)
        before = expense_count_for_user(DEMO_USER_ID)
        client.post(ADD_EXPENSE_URL, data=valid_form(date=bad_date))
        after = expense_count_for_user(DEMO_USER_ID)
        assert after == before, "No row should be created when the date is invalid"


# ------------------------------------------------------------------ #
# Combined / edge cases — must never 500                              #
# ------------------------------------------------------------------ #

class TestAddExpenseNeverServerErrors:
    @pytest.mark.parametrize(
        "overrides",
        [
            {"amount": "-1", "category": "Bad", "date": "bad"},
            {"amount": "", "date": ""},
            {"category": ""},
            {"amount": "not-a-number", "category": "not-a-category", "date": "not-a-date"},
            {"amount": "9" * 200},  # very long numeric-looking string
            {"description": "x" * 5000},  # very long description
        ],
    )
    def test_bad_combinations_never_return_server_error(self, client, overrides):
        login(client)
        response = client.post(ADD_EXPENSE_URL, data=valid_form(**overrides))
        assert_no_server_error(response)


# ------------------------------------------------------------------ #
# Definition-of-done: profile integration                             #
# ------------------------------------------------------------------ #

class TestAddExpenseProfileIntegration:
    def test_new_expense_appears_in_recent_transactions_on_profile(self, client):
        login(client)
        client.post(
            ADD_EXPENSE_URL,
            data=valid_form(amount="77.77", category="Health", date=date.today().isoformat(), description="Dentist visit"),
        )
        response = client.get(PROFILE_URL)
        body = response.get_data(as_text=True)
        assert "Dentist visit" in body, "Newly added expense should show up in recent transactions"

    def test_new_expense_increases_total_spent_stat(self, client):
        login(client)
        before_response = client.get(PROFILE_URL)
        before_body = before_response.get_data(as_text=True)

        client.post(
            ADD_EXPENSE_URL,
            data=valid_form(amount="500.00", category="Other", date=date.today().isoformat(), description="Big purchase"),
        )

        after_response = client.get(PROFILE_URL)
        after_body = after_response.get_data(as_text=True)
        assert after_body != before_body, "Profile stats should change after adding an expense"
        assert "Big purchase" in after_body

    def test_new_expense_reflected_in_category_breakdown(self, client):
        login(client)
        client.post(
            ADD_EXPENSE_URL,
            data=valid_form(amount="60.00", category="Entertainment", date=date.today().isoformat(), description="Concert ticket"),
        )
        response = client.get(PROFILE_URL)
        body = response.get_data(as_text=True)
        assert "Entertainment" in body
        assert "Category breakdown" in body

    def test_add_expense_link_visible_on_profile_page(self, client):
        login(client)
        response = client.get(PROFILE_URL)
        body = response.get_data(as_text=True)
        assert ADD_EXPENSE_URL in body, "Profile page should contain a visible link/button to add an expense"
