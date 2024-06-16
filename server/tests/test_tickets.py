from app.models import TicketEvent, TicketEventType, TicketPriority, TicketStatus
from tests.conftest import auth_headers


def test_customer_creates_ticket(client, db, customer):
    response = client.post(
        "/api/tickets",
        headers=auth_headers(customer),
        json={"subject": "Invoice is wrong", "description": "I was charged twice this month."},
    )

    assert response.status_code == 201
    ticket = response.json()
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "MEDIUM"
    assert ticket["customer"]["id"] == customer.id
    assert ticket["assigned_agent"] is None

    events = db.query(TicketEvent).filter_by(ticket_id=ticket["id"]).all()
    assert [event.event_type for event in events] == [TicketEventType.TICKET_CREATED]


def test_ticket_creation_validates_input(client, customer):
    response = client.post(
        "/api/tickets", headers=auth_headers(customer), json={"subject": "", "description": "x"}
    )

    assert response.status_code == 422


def test_staff_cannot_create_tickets_as_customers(client, agent):
    response = client.post(
        "/api/tickets",
        headers=auth_headers(agent),
        json={"subject": "Hello there", "description": "Some description here"},
    )

    assert response.status_code == 403


def test_customer_only_sees_own_tickets(client, customer, other_customer, make_ticket):
    own = make_ticket(customer)
    make_ticket(other_customer)

    response = client.get("/api/tickets", headers=auth_headers(customer))

    assert response.status_code == 200
    assert [ticket["id"] for ticket in response.json()["items"]] == [own.id]


def test_customer_cannot_filter_their_way_into_other_tickets(
    client, customer, other_customer, make_ticket
):
    make_ticket(other_customer)

    response = client.get(
        f"/api/tickets?customer_id={other_customer.id}", headers=auth_headers(customer)
    )

    assert response.json()["total"] == 0


def test_customer_cannot_open_another_customers_ticket(
    client, customer, other_customer, make_ticket
):
    ticket = make_ticket(other_customer)

    response = client.get(f"/api/tickets/{ticket.id}", headers=auth_headers(customer))

    assert response.status_code == 404


def test_customer_does_not_receive_ai_fields(client, customer, make_ticket):
    ticket = make_ticket(customer, ai_summary="Angry customer", ai_sentiment="NEGATIVE")

    body = client.get(f"/api/tickets/{ticket.id}", headers=auth_headers(customer)).json()

    assert body["ai_summary"] is None
    assert body["ai_sentiment"] is None


def test_agent_sees_ai_fields(client, agent, customer, make_ticket):
    ticket = make_ticket(customer, ai_summary="Login problem", ai_sentiment="NEGATIVE")

    body = client.get(f"/api/tickets/{ticket.id}", headers=auth_headers(agent)).json()

    assert body["ai_summary"] == "Login problem"
    assert body["ai_sentiment"] == "NEGATIVE"


def test_agent_sees_all_tickets(client, agent, customer, other_customer, make_ticket):
    make_ticket(customer)
    make_ticket(other_customer)

    response = client.get("/api/tickets", headers=auth_headers(agent))

    assert response.json()["total"] == 2


def test_list_requires_authentication(client):
    assert client.get("/api/tickets").status_code == 401


def test_filter_by_status_priority_and_category(client, agent, customer, make_ticket):
    match = make_ticket(
        customer,
        status=TicketStatus.IN_PROGRESS,
        priority=TicketPriority.URGENT,
        category="BILLING",
    )
    make_ticket(
        customer, status=TicketStatus.IN_PROGRESS, priority=TicketPriority.LOW, category="BILLING"
    )
    make_ticket(
        customer, status=TicketStatus.OPEN, priority=TicketPriority.URGENT, category="BILLING"
    )
    make_ticket(
        customer, status=TicketStatus.IN_PROGRESS, priority=TicketPriority.URGENT, category="BUG"
    )

    response = client.get(
        "/api/tickets?status=IN_PROGRESS&priority=URGENT&category=BILLING",
        headers=auth_headers(agent),
    )

    assert [ticket["id"] for ticket in response.json()["items"]] == [match.id]


def test_filter_accepts_multiple_statuses(client, agent, customer, make_ticket):
    make_ticket(customer, status=TicketStatus.OPEN)
    make_ticket(customer, status=TicketStatus.IN_PROGRESS)
    make_ticket(customer, status=TicketStatus.CLOSED)

    response = client.get(
        "/api/tickets?status=OPEN&status=IN_PROGRESS", headers=auth_headers(agent)
    )

    assert response.json()["total"] == 2


def test_filter_by_assigned_agent(client, agent, make_user, customer, make_ticket):
    other_agent = make_user(role=agent.role)
    mine = make_ticket(customer, assigned_agent_id=agent.id)
    unassigned = make_ticket(customer)
    theirs = make_ticket(customer, assigned_agent_id=other_agent.id)
    headers = auth_headers(agent)

    def ids(query):
        return [
            t["id"] for t in client.get(f"/api/tickets?{query}", headers=headers).json()["items"]
        ]

    assert ids("assigned_agent=me") == [mine.id]
    assert ids("assigned_agent=unassigned") == [unassigned.id]
    assert ids(f"assigned_agent={other_agent.id}") == [theirs.id]
    assert client.get("/api/tickets?assigned_agent=bogus", headers=headers).status_code == 422


def test_search_matches_subject_description_and_customer(client, agent, customer, make_ticket):
    by_subject = make_ticket(customer, subject="Password reset email never arrives")
    by_description = make_ticket(
        customer, subject="Help", description="The invoices page shows the wrong currency"
    )
    make_ticket(customer, subject="Unrelated", description="Dark mode request for the editor")
    headers = auth_headers(agent)

    def ids(term):
        response = client.get("/api/tickets", params={"search": term}, headers=headers)
        return {t["id"] for t in response.json()["items"]}

    assert ids("password") == {by_subject.id}
    assert ids("invoice currency") == {by_description.id}
    assert ids("pass") == {by_subject.id}
    assert ids(f"#{by_description.id}") == {by_description.id}
    assert len(ids(customer.email)) == 3


def test_pagination(client, agent, customer, make_ticket):
    for index in range(25):
        make_ticket(customer, subject=f"Ticket number {index}")

    response = client.get("/api/tickets?page=2&page_size=10", headers=auth_headers(agent))
    body = response.json()

    assert body["total"] == 25
    assert body["page"] == 2
    assert body["pages"] == 3
    assert len(body["items"]) == 10


def test_sort_by_priority(client, agent, customer, make_ticket):
    low = make_ticket(customer, priority=TicketPriority.LOW)
    urgent = make_ticket(customer, priority=TicketPriority.URGENT)
    high = make_ticket(customer, priority=TicketPriority.HIGH)

    response = client.get("/api/tickets?sort=priority&order=desc", headers=auth_headers(agent))

    assert [t["id"] for t in response.json()["items"]] == [urgent.id, high.id, low.id]


def test_agent_changes_status_and_priority(client, db, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    response = client.patch(
        f"/api/tickets/{ticket.id}",
        headers=auth_headers(agent),
        json={"status": "RESOLVED", "priority": "HIGH", "category": "TECHNICAL"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RESOLVED"
    assert body["priority"] == "HIGH"
    assert body["category"] == "TECHNICAL"
    assert body["resolved_at"] is not None

    event_types = [e.event_type for e in db.query(TicketEvent).filter_by(ticket_id=ticket.id)]
    assert TicketEventType.STATUS_CHANGED in event_types
    assert TicketEventType.PRIORITY_CHANGED in event_types
    assert TicketEventType.CATEGORY_CHANGED in event_types
    assert TicketEventType.TICKET_RESOLVED in event_types


def test_reopening_clears_resolved_at(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    headers = auth_headers(agent)
    client.patch(f"/api/tickets/{ticket.id}", headers=headers, json={"status": "RESOLVED"})

    body = client.patch(
        f"/api/tickets/{ticket.id}", headers=headers, json={"status": "IN_PROGRESS"}
    ).json()

    assert body["resolved_at"] is None


def test_unknown_category_is_rejected(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    response = client.patch(
        f"/api/tickets/{ticket.id}", headers=auth_headers(agent), json={"category": "NOPE"}
    )

    assert response.status_code == 400


def test_agent_cannot_change_ticket_assigned_to_someone_else(
    client, agent, make_user, customer, make_ticket
):
    other_agent = make_user(role=agent.role)
    ticket = make_ticket(customer, assigned_agent_id=other_agent.id)

    response = client.patch(
        f"/api/tickets/{ticket.id}", headers=auth_headers(agent), json={"priority": "LOW"}
    )

    assert response.status_code == 403


def test_admin_can_change_any_ticket(client, admin, agent, customer, make_ticket):
    ticket = make_ticket(customer, assigned_agent_id=agent.id)

    response = client.patch(
        f"/api/tickets/{ticket.id}", headers=auth_headers(admin), json={"priority": "URGENT"}
    )

    assert response.status_code == 200


def test_customer_can_close_own_ticket(client, customer, make_ticket):
    ticket = make_ticket(customer)

    response = client.patch(
        f"/api/tickets/{ticket.id}", headers=auth_headers(customer), json={"status": "CLOSED"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CLOSED"


def test_customer_cannot_change_priority_or_other_statuses(client, customer, make_ticket):
    ticket = make_ticket(customer)
    headers = auth_headers(customer)

    assert (
        client.patch(
            f"/api/tickets/{ticket.id}", headers=headers, json={"priority": "URGENT"}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/tickets/{ticket.id}", headers=headers, json={"status": "RESOLVED"}
        ).status_code
        == 403
    )


def test_customer_cannot_close_another_customers_ticket(
    client, customer, other_customer, make_ticket
):
    ticket = make_ticket(other_customer)

    response = client.patch(
        f"/api/tickets/{ticket.id}", headers=auth_headers(customer), json={"status": "CLOSED"}
    )

    assert response.status_code == 404


def test_only_admin_can_delete(client, admin, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    assert (
        client.delete(f"/api/tickets/{ticket.id}", headers=auth_headers(customer)).status_code
        == 403
    )
    assert (
        client.delete(f"/api/tickets/{ticket.id}", headers=auth_headers(agent)).status_code == 403
    )
    assert (
        client.delete(f"/api/tickets/{ticket.id}", headers=auth_headers(admin)).status_code == 204
    )
    assert client.get(f"/api/tickets/{ticket.id}", headers=auth_headers(admin)).status_code == 404


def test_ticket_history(client, agent, customer, make_ticket):
    created = client.post(
        "/api/tickets",
        headers=auth_headers(customer),
        json={"subject": "Export fails", "description": "CSV export spins forever."},
    ).json()
    client.patch(
        f"/api/tickets/{created['id']}", headers=auth_headers(agent), json={"status": "IN_PROGRESS"}
    )

    events = client.get(
        f"/api/tickets/{created['id']}/events", headers=auth_headers(customer)
    ).json()

    assert [e["event_type"] for e in events] == ["TICKET_CREATED", "STATUS_CHANGED"]
    assert events[1]["metadata"] == {"from": "OPEN", "to": "IN_PROGRESS"}
    assert events[1]["user"]["id"] == agent.id


def test_customer_history_hides_ai_events(client, db, customer, make_ticket):
    ticket = make_ticket(customer)
    db.add(
        TicketEvent(
            ticket_id=ticket.id, event_type=TicketEventType.AI_ANALYSIS_COMPLETED, metadata_={}
        )
    )
    db.commit()

    events = client.get(f"/api/tickets/{ticket.id}/events", headers=auth_headers(customer)).json()

    assert events == []
