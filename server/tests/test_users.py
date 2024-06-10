from app.models import UserRole
from tests.conftest import auth_headers


def test_admin_can_list_users(client, admin, customer, agent):
    response = client.get("/api/users", headers=auth_headers(admin))

    assert response.status_code == 200
    assert response.json()["total"] == 3


def test_admin_can_filter_users_by_role(client, admin, customer, agent):
    response = client.get("/api/users?role=AGENT", headers=auth_headers(admin))

    assert [user["id"] for user in response.json()["items"]] == [agent.id]


def test_non_admins_cannot_manage_users(client, agent, customer):
    assert client.get("/api/users", headers=auth_headers(agent)).status_code == 403
    assert client.get("/api/users", headers=auth_headers(customer)).status_code == 403
    response = client.post(
        "/api/users",
        headers=auth_headers(agent),
        json={"email": "a@example.com", "name": "A", "password": "password123", "role": "ADMIN"},
    )
    assert response.status_code == 403


def test_admin_can_create_agent(client, admin):
    response = client.post(
        "/api/users",
        headers=auth_headers(admin),
        json={
            "email": "new.agent@example.com",
            "name": "New Agent",
            "password": "password123",
            "role": "AGENT",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == "AGENT"


def test_admin_can_change_role_and_deactivate(client, admin, customer):
    response = client.patch(
        f"/api/users/{customer.id}",
        headers=auth_headers(admin),
        json={"role": "AGENT", "is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "AGENT"
    assert response.json()["is_active"] is False


def test_admin_cannot_demote_themselves(client, admin):
    response = client.patch(
        f"/api/users/{admin.id}", headers=auth_headers(admin), json={"role": "AGENT"}
    )

    assert response.status_code == 400


def test_agents_list_only_includes_active_staff(client, agent, admin, customer, make_user):
    make_user(UserRole.AGENT, is_active=False)

    response = client.get("/api/users/agents", headers=auth_headers(agent))

    assert response.status_code == 200
    assert {user["id"] for user in response.json()} == {agent.id, admin.id}


def test_customer_cannot_list_agents(client, customer):
    assert client.get("/api/users/agents", headers=auth_headers(customer)).status_code == 403
