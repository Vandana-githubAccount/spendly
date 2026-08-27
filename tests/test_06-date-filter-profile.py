"""Tests for the date-range filter on the profile page.

Spec: .claude/specs/06-date-filter-profile.md

Covers:
- Default (no query params) behaves as all-time, same as before this feature.
- Preset ranges (7d, 30d, month) return 200 and mark themselves as selected.
- Valid custom range returns 200 and retains the submitted start/end values.
- Invalid custom input (malformed date, start > end, missing start/end) never
  raises a server error (always 200) and falls back to all-time data with a
  friendly inline message.
- Auth guard: /profile (with or without query params) redirects to /login
  when not logged in.
- A range with zero matching expenses renders the documented zero-state
  (total_spent 0.00, transaction_count 0, top_category em-dash, no rows).
"""

import pytest


def login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1


class TestProfileDateFilterAuthGuard:
    """Mirrors the existing test_profile.py auth-guard pattern, extended to
    cover the new query-string parameters."""

    @pytest.mark.parametrize(
        "query_string",
        [
            "",
            "?range=7d",
            "?range=30d",
            "?range=month",
            "?range=custom&start=2026-01-01&end=2026-01-31",
        ],
    )
    def test_profile_redirects_when_logged_out(self, client, query_string):
        response = client.get(f"/profile{query_string}")
        assert response.status_code == 302, "Unauthenticated /profile should redirect"
        assert "/login" in response.headers["Location"], "Should redirect to login"


class TestProfileDefaultRange:
    """GET /profile with no query params should behave exactly as before
    this feature (all-time data)."""

    def test_no_query_params_returns_200(self, client):
        login(client)
        response = client.get("/profile")
        assert response.status_code == 200

    def test_no_query_params_shows_alltime_sections(self, client):
        login(client)
        response = client.get("/profile")
        body = response.get_data(as_text=True)

        assert "Total spent" in body
        assert "Transactions" in body
        assert "Top category" in body
        # Same seeded demo data used before this feature existed.
        assert "Lunch" in body
        assert "Fuel" in body
        assert "Electricity bill" in body

    def test_no_query_params_defaults_to_all_time_selected(self, client):
        login(client)
        response = client.get("/profile")
        body = response.get_data(as_text=True)
        assert 'value="all" selected' in body, "All time should be the default selection"


class TestProfilePresetRanges:
    """?range=7d / 30d / month must all succeed without error."""

    @pytest.mark.parametrize("range_value", ["7d", "30d", "month"])
    def test_preset_range_returns_200(self, client, range_value):
        login(client)
        response = client.get(f"/profile?range={range_value}")
        assert response.status_code == 200, f"range={range_value} should not error"

    @pytest.mark.parametrize("range_value", ["7d", "30d", "month"])
    def test_preset_range_is_marked_selected(self, client, range_value):
        login(client)
        response = client.get(f"/profile?range={range_value}")
        body = response.get_data(as_text=True)
        assert f'value="{range_value}" selected' in body, (
            f"Filter control should reflect range={range_value} as selected"
        )

    @pytest.mark.parametrize("range_value", ["7d", "30d", "month"])
    def test_preset_range_still_renders_core_sections(self, client, range_value):
        login(client)
        response = client.get(f"/profile?range={range_value}")
        body = response.get_data(as_text=True)
        assert "Total spent" in body
        assert "Transactions" in body
        assert "Top category" in body
        assert "Recent transactions" in body
        assert "Category breakdown" in body


class TestProfileCustomRangeValid:
    """A valid custom range (start <= end) should filter successfully and
    retain the submitted values in the UI."""

    def test_valid_custom_range_returns_200(self, client):
        login(client)
        response = client.get("/profile?range=custom&start=2020-01-01&end=2030-01-01")
        assert response.status_code == 200

    def test_valid_custom_range_marks_custom_selected(self, client):
        login(client)
        response = client.get("/profile?range=custom&start=2020-01-01&end=2030-01-01")
        body = response.get_data(as_text=True)
        assert 'value="custom" selected' in body

    def test_valid_custom_range_retains_submitted_dates(self, client):
        login(client)
        response = client.get("/profile?range=custom&start=2020-01-01&end=2030-01-01")
        body = response.get_data(as_text=True)
        assert 'value="2020-01-01"' in body, "Start date input should retain submitted value"
        assert 'value="2030-01-01"' in body, "End date input should retain submitted value"

    def test_valid_custom_range_wide_window_includes_seed_data(self, client):
        login(client)
        # Window wide enough to include all seeded demo expenses (they're all
        # recent, within the last 8 days).
        response = client.get("/profile?range=custom&start=2020-01-01&end=2030-01-01")
        body = response.get_data(as_text=True)
        assert "Lunch" in body
        assert "Fuel" in body
        assert "Electricity bill" in body


class TestProfileCustomRangeInvalid:
    """Invalid custom range input must never 500 and must fall back to
    all-time data with a friendly inline message, per the spec's explicit
    rule."""

    def test_start_after_end_returns_200(self, client):
        login(client)
        response = client.get("/profile?range=custom&start=2026-06-01&end=2026-01-01")
        assert response.status_code == 200, "start > end must not cause a server error"

    def test_start_after_end_shows_inline_message(self, client):
        login(client)
        response = client.get("/profile?range=custom&start=2026-06-01&end=2026-01-01")
        body = response.get_data(as_text=True)
        assert 'class="auth-error"' in body, "A friendly inline message should be shown"

    def test_start_after_end_falls_back_to_alltime_data(self, client):
        login(client)
        response = client.get("/profile?range=custom&start=2026-06-01&end=2026-01-01")
        body = response.get_data(as_text=True)
        # Falls back to all-time, so the normal seeded data is still visible.
        assert "Lunch" in body
        assert "Fuel" in body
        assert "Electricity bill" in body

    @pytest.mark.parametrize(
        "bad_start,bad_end",
        [
            ("not-a-date", "2026-01-31"),
            ("2026-01-01", "not-a-date"),
            ("2026-13-40", "2026-01-31"),
            ("31/01/2026", "01/02/2026"),
        ],
    )
    def test_malformed_dates_return_200(self, client, bad_start, bad_end):
        login(client)
        response = client.get(f"/profile?range=custom&start={bad_start}&end={bad_end}")
        assert response.status_code == 200, "Malformed dates must never cause a server error"

    def test_missing_start_returns_200(self, client):
        login(client)
        response = client.get("/profile?range=custom&end=2026-01-31")
        assert response.status_code == 200, "Missing start must not cause a server error"

    def test_missing_end_returns_200(self, client):
        login(client)
        response = client.get("/profile?range=custom&start=2026-01-01")
        assert response.status_code == 200, "Missing end must not cause a server error"

    def test_missing_both_start_and_end_returns_200(self, client):
        login(client)
        response = client.get("/profile?range=custom")
        assert response.status_code == 200, "Missing both start and end must not cause a server error"

    def test_invalid_range_never_returns_server_error(self, client):
        login(client)
        cases = [
            "/profile?range=custom&start=2026-06-01&end=2026-01-01",
            "/profile?range=custom&start=garbage&end=2026-01-31",
            "/profile?range=custom",
            "/profile?range=custom&start=2026-01-01",
        ]
        for path in cases:
            response = client.get(path)
            assert response.status_code < 500, f"{path} must never raise a server error"


class TestProfileZeroStateForOutOfRangeCustomFilter:
    """A custom range with zero matching expenses must render the documented
    zero-state, not an error and not stale data."""

    @pytest.fixture
    def empty_range_response(self, client):
        login(client)
        # Seed data is all recent (within the last ~8 days from "today"), so
        # this early-2020 window is guaranteed to have no matches.
        return client.get("/profile?range=custom&start=2020-01-01&end=2020-01-02")

    def test_returns_200(self, empty_range_response):
        assert empty_range_response.status_code == 200

    def test_zero_total_spent(self, empty_range_response):
        body = empty_range_response.get_data(as_text=True)
        assert "₹0.00" in body, "Total spent should be formatted as 0.00 when no expenses match"

    def test_zero_transaction_count(self, empty_range_response):
        body = empty_range_response.get_data(as_text=True)
        assert ">0<" in body, "Transaction count should be 0 when no expenses match"

    def test_top_category_placeholder(self, empty_range_response):
        body = empty_range_response.get_data(as_text=True)
        assert "—" in body, "Top category should show an em dash placeholder when no expenses match"

    def test_no_seeded_transactions_appear(self, empty_range_response):
        body = empty_range_response.get_data(as_text=True)
        assert "Lunch" not in body
        assert "Fuel" not in body
        assert "Electricity bill" not in body

    def test_no_server_error(self, empty_range_response):
        body = empty_range_response.get_data(as_text=True)
        assert "Traceback" not in body
        assert "Internal Server Error" not in body
