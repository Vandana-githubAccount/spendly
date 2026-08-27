def test_profile_redirects_when_logged_out(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_ok_when_logged_in(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile")
    assert response.status_code == 200


def test_profile_shows_expected_sections(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "Member since" in body

    assert "Total spent" in body
    assert "Transactions" in body
    assert "Top category" in body

    assert "badge-food" in body
    assert "badge-transport" in body
    assert "badge-bills" in body

    assert "Lunch" in body
    assert "Fuel" in body
    assert "Electricity bill" in body
