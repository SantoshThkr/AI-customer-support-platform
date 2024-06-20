from app.models import TicketAssignment, UserRole
from tests.conftest import auth_headers


def assign(client, user, ticket, agent_id):
    return client.post(
        f"/api/tickets/{ticket.id}/assign",
        headers=auth_headers(user),
        json={"agent_id": agent_id},
    )


def test_agent_picks_up_unassigned_ticket(client, db, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    response = assign(client, agent, ticket, agent.id)

    assert response.status_code == 200
    assert response.json()["assigned_agent"]["id"] == agent.id
    assignment = db.query(TicketAssignment).filter_by(ticket_id=ticket.id).one()
    assert assignment.agent_id == agent.id
    assert assignment.assigned_by_id == agent.id


def test_assignment_is_recorded_in_history(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    assign(client, agent, ticket, agent.id)

    events = client.get(f"/api/tickets/{ticket.id}/events", headers=auth_headers(agent)).json()

    assert events[-1]["event_type"] == "TICKET_ASSIGNED"
    assert events[-1]["metadata"]["agent_id"] == agent.id
    assert events[-1]["metadata"]["agent_name"] == agent.name


def test_agent_hands_off_own_ticket(client, agent, make_user, customer, make_ticket):
    colleague = make_user(UserRole.AGENT)
    ticket = make_ticket(customer, assigned_agent_id=agent.id)

    response = assign(client, agent, ticket, colleague.id)

    assert response.json()["assigned_agent"]["id"] == colleague.id


def test_agent_cannot_take_another_agents_ticket(client, agent, make_user, customer, make_ticket):
    colleague = make_user(UserRole.AGENT)
    ticket = make_ticket(customer, assigned_agent_id=colleague.id)

    assert assign(client, agent, ticket, agent.id).status_code == 403


def test_admin_can_reassign(client, admin, agent, make_user, customer, make_ticket):
    colleague = make_user(UserRole.AGENT)
    ticket = make_ticket(customer, assigned_agent_id=colleague.id)

    assert assign(client, admin, ticket, agent.id).status_code == 200


def test_unassign(client, agent, customer, make_ticket):
    ticket = make_ticket(customer, assigned_agent_id=agent.id)

    response = assign(client, agent, ticket, None)

    assert response.status_code == 200
    assert response.json()["assigned_agent"] is None


def test_cannot_assign_to_customer_or_inactive_agent(
    client, admin, make_user, customer, make_ticket
):
    inactive = make_user(UserRole.AGENT, is_active=False)
    ticket = make_ticket(customer)

    assert assign(client, admin, ticket, customer.id).status_code == 400
    assert assign(client, admin, ticket, inactive.id).status_code == 400
    assert assign(client, admin, ticket, 9999).status_code == 400


def test_customer_cannot_assign(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    assert assign(client, customer, ticket, agent.id).status_code == 403
