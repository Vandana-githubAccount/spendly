from database.db import create_user
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
)

DEMO_USER_ID = 1


def _make_empty_user():
    return create_user("Empty User", "empty@spendly.com", "not-a-real-hash")


# ------------------------------------------------------------------ #
# Unit tests: get_summary_stats                                       #
# ------------------------------------------------------------------ #

def test_get_summary_stats_with_expenses(app):
    stats = get_summary_stats(DEMO_USER_ID)
    assert stats["total_spent"] == 346.24
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(app):
    user_id = _make_empty_user()
    stats = get_summary_stats(user_id)
    assert stats["total_spent"] == 0.0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


# ------------------------------------------------------------------ #
# Unit tests: get_recent_transactions                                 #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_newest_first(app):
    transactions = get_recent_transactions(DEMO_USER_ID)
    assert len(transactions) == 8
    assert transactions[0]["description"] == "Lunch"
    dates = [tx["date"] for tx in transactions]
    assert dates == sorted(dates, reverse=True)


def test_get_recent_transactions_limit(app):
    transactions = get_recent_transactions(DEMO_USER_ID, limit=3)
    assert len(transactions) == 3


def test_get_recent_transactions_no_expenses(app):
    user_id = _make_empty_user()
    assert get_recent_transactions(user_id) == []


# ------------------------------------------------------------------ #
# Unit tests: get_category_breakdown                                  #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_sums_to_100(app):
    categories = get_category_breakdown(DEMO_USER_ID)
    assert len(categories) == 7
    assert categories[0]["name"] == "Bills"
    assert sum(cat["percent"] for cat in categories) == 100
    totals = [cat["total"] for cat in categories]
    assert totals == sorted(totals, reverse=True)


def test_get_category_breakdown_no_expenses(app):
    user_id = _make_empty_user()
    assert get_category_breakdown(user_id) == []


# ------------------------------------------------------------------ #
# Route tests                                                         #
# ------------------------------------------------------------------ #

def test_profile_route_requires_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_route_shows_real_data(client):
    with client.session_transaction() as sess:
        sess["user_id"] = DEMO_USER_ID

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "₹346.24" in body
    assert "Bills" in body
    assert "Lunch" in body

    for category in ("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"):
        assert category in body


def test_profile_route_uses_css_classes_not_inline_styles(client):
    with client.session_transaction() as sess:
        sess["user_id"] = DEMO_USER_ID

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert 'style="width' not in body
    assert "bar-w-" in body


def test_profile_route_empty_state_for_new_user(client):
    user_id = _make_empty_user()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹0.00" in body
    assert "Traceback" not in body
