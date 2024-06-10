from app.models import UserRole
from tests.conftest import PASSWORD, auth_headers


def register(client, email="new@example.com", password="secret-pass-1", name="New User"):
    return client.post(
        "/api/auth/register", json={"email": email, "password": password, "name": name}
    )


def test_register_creates_customer_and_returns_token(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["role"] == "CUSTOMER"
    assert "password_hash" not in body["user"]


def test_register_ignores_role_in_payload(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "x@example.com", "password": "secret-pass-1", "name": "X", "role": "ADMIN"},
    )

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "CUSTOMER"


def test_register_duplicate_email_is_rejected(client):
    register(client, email="dup@example.com")

    response = register(client, email="DUP@example.com")

    assert response.status_code == 409


def test_register_validates_input(client):
    response = register(client, email="not-an-email", password="short")

    assert response.status_code == 422


def test_login_success(client, customer):
    response = client.post("/api/auth/login", json={"email": customer.email, "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["user"]["id"] == customer.id


def test_login_is_case_insensitive_for_email(client, customer):
    response = client.post(
        "/api/auth/login", json={"email": customer.email.upper(), "password": PASSWORD}
    )

    assert response.status_code == 200


def test_login_with_wrong_password(client, customer):
    response = client.post(
        "/api/auth/login", json={"email": customer.email, "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_login_with_unknown_email(client):
    response = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert response.status_code == 401


def test_inactive_user_cannot_login(client, make_user):
    user = make_user(UserRole.CUSTOMER, is_active=False)

    response = client.post("/api/auth/login", json={"email": user.email, "password": PASSWORD})

    assert response.status_code == 403


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_returns_current_user(client, agent):
    response = client.get("/api/auth/me", headers=auth_headers(agent))

    assert response.status_code == 200
    assert response.json()["role"] == "AGENT"


def test_token_of_deactivated_user_stops_working(client, db, customer):
    headers = auth_headers(customer)
    customer.is_active = False
    db.commit()

    assert client.get("/api/auth/me", headers=headers).status_code == 401
