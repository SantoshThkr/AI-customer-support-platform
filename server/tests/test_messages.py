from app.models import TicketEvent, TicketEventType, TicketStatus
from tests.conftest import auth_headers


def post_message(client, user, ticket, text="Hello", is_internal=False):
    return client.post(
        f"/api/tickets/{ticket.id}/messages",
        headers=auth_headers(user),
        json={"message": text, "is_internal": is_internal},
    )


def test_customer_replies_to_own_ticket(client, db, customer, make_ticket):
    ticket = make_ticket(customer)

    response = post_message(client, customer, ticket, "Any update on this?")

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Any update on this?"
    assert body["is_internal"] is False
    assert body["sender"]["id"] == customer.id

    event = db.query(TicketEvent).filter_by(ticket_id=ticket.id).one()
    assert event.event_type == TicketEventType.MESSAGE_ADDED
    assert event.metadata_ == {"message_id": body["id"], "is_internal": False}


def test_agent_replies_to_customer(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    response = post_message(client, agent, ticket, "Could you try clearing your cache?")

    assert response.status_code == 201
    messages = client.get(
        f"/api/tickets/{ticket.id}/messages", headers=auth_headers(customer)
    ).json()
    assert [m["message"] for m in messages] == ["Could you try clearing your cache?"]


def test_agent_adds_internal_note(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    response = post_message(client, agent, ticket, "Looks like the SSO bug", is_internal=True)

    assert response.status_code == 201
    assert response.json()["is_internal"] is True


def test_customer_cannot_see_internal_notes(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    post_message(client, agent, ticket, "Public reply")
    post_message(client, agent, ticket, "Customer seems confused", is_internal=True)

    customer_view = client.get(
        f"/api/tickets/{ticket.id}/messages", headers=auth_headers(customer)
    ).json()
    agent_view = client.get(
        f"/api/tickets/{ticket.id}/messages", headers=auth_headers(agent)
    ).json()

    assert [m["message"] for m in customer_view] == ["Public reply"]
    assert len(agent_view) == 2


def test_customer_history_hides_internal_note_events(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    post_message(client, agent, ticket, "Internal", is_internal=True)

    events = client.get(f"/api/tickets/{ticket.id}/events", headers=auth_headers(customer)).json()

    assert events == []


def test_customer_cannot_create_internal_note(client, customer, make_ticket):
    ticket = make_ticket(customer)

    response = post_message(client, customer, ticket, "Sneaky", is_internal=True)

    assert response.status_code == 403


def test_customer_cannot_access_other_customers_messages(
    client, customer, other_customer, make_ticket
):
    ticket = make_ticket(other_customer)

    assert (
        client.get(f"/api/tickets/{ticket.id}/messages", headers=auth_headers(customer)).status_code
        == 404
    )
    assert post_message(client, customer, ticket).status_code == 404


def test_messages_require_authentication(client, customer, make_ticket):
    ticket = make_ticket(customer)

    assert client.get(f"/api/tickets/{ticket.id}/messages").status_code == 401


def test_agent_cannot_reply_on_another_agents_ticket_but_can_add_note(
    client, agent, make_user, customer, make_ticket
):
    other_agent = make_user(role=agent.role)
    ticket = make_ticket(customer, assigned_agent_id=other_agent.id)

    assert post_message(client, agent, ticket, "Reply").status_code == 403
    assert post_message(client, agent, ticket, "FYI", is_internal=True).status_code == 201


def test_admin_can_reply_to_any_ticket(client, admin, agent, customer, make_ticket):
    ticket = make_ticket(customer, assigned_agent_id=agent.id)

    assert post_message(client, admin, ticket, "Jumping in").status_code == 201


def test_customer_reply_reopens_waiting_ticket(client, agent, customer, make_ticket):
    ticket = make_ticket(
        customer, status=TicketStatus.WAITING_FOR_CUSTOMER, assigned_agent_id=agent.id
    )

    post_message(client, customer, ticket, "Here are the details you asked for")

    body = client.get(f"/api/tickets/{ticket.id}", headers=auth_headers(customer)).json()
    assert body["status"] == "IN_PROGRESS"


def test_customer_cannot_reply_to_closed_ticket(client, customer, make_ticket):
    ticket = make_ticket(customer, status=TicketStatus.CLOSED)

    assert post_message(client, customer, ticket).status_code == 409


def test_empty_message_is_rejected(client, customer, make_ticket):
    ticket = make_ticket(customer)

    assert post_message(client, customer, ticket, "").status_code == 422
