from tests.conftest import auth_headers


def test_default_categories_exist(client, customer):
    response = client.get("/api/categories", headers=auth_headers(customer))

    codes = {category["code"] for category in response.json()}
    assert {
        "ACCOUNT",
        "BILLING",
        "TECHNICAL",
        "BUG",
        "FEATURE_REQUEST",
        "SECURITY",
        "OTHER",
    } <= codes


def test_admin_creates_and_deactivates_category(client, admin, customer):
    created = client.post(
        "/api/categories",
        headers=auth_headers(admin),
        json={"code": "ONBOARDING", "name": "Onboarding", "description": "New customer setup"},
    )
    assert created.status_code == 201

    client.patch(
        f"/api/categories/{created.json()['id']}",
        headers=auth_headers(admin),
        json={"is_active": False},
    )

    customer_view = client.get("/api/categories", headers=auth_headers(customer)).json()
    assert "ONBOARDING" not in {category["code"] for category in customer_view}
    admin_view = client.get(
        "/api/categories?include_inactive=true", headers=auth_headers(admin)
    ).json()
    assert "ONBOARDING" in {category["code"] for category in admin_view}


def test_duplicate_category_code(client, admin):
    response = client.post(
        "/api/categories", headers=auth_headers(admin), json={"code": "BILLING", "name": "Dup"}
    )

    assert response.status_code == 409


def test_category_code_format(client, admin):
    response = client.post(
        "/api/categories", headers=auth_headers(admin), json={"code": "bad code", "name": "Bad"}
    )

    assert response.status_code == 422


def test_agent_cannot_manage_categories(client, agent):
    response = client.post(
        "/api/categories", headers=auth_headers(agent), json={"code": "NEW", "name": "New"}
    )

    assert response.status_code == 403
