from app.dependencies.ai import ai_rate_limiter
from app.models import AIOperation, AIUsage, Ticket, TicketEvent, TicketEventType
from tests.conftest import auth_headers
from tests.fakes import analysis_json, chat_response, timeout_error


def analyze(client, user, ticket):
    return client.post(f"/api/ai/tickets/{ticket.id}/analyze", headers=auth_headers(user))


def test_valid_classification_updates_ticket(client, db, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    fake_openai.queue(chat_response(analysis_json(category="ACCOUNT", priority="URGENT")))

    response = analyze(client, agent, ticket)

    assert response.status_code == 200
    assert response.json() == {
        "category": "ACCOUNT",
        "priority": "URGENT",
        "sentiment": "NEGATIVE",
        "summary": "Customer cannot log in after resetting their password.",
    }
    db.refresh(ticket)
    assert ticket.category == "ACCOUNT"
    assert ticket.priority.value == "URGENT"
    assert ticket.ai_sentiment.value == "NEGATIVE"
    assert ticket.ai_summary.startswith("Customer cannot log in")

    event = db.query(TicketEvent).filter_by(event_type=TicketEventType.AI_ANALYSIS_COMPLETED).one()
    assert event.metadata_["previous_priority"] == "MEDIUM"


def test_prompt_contains_ticket_and_categories(client, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer, subject="Refund please", description="I was double charged.")
    fake_openai.queue(chat_response(analysis_json(category="BILLING")))

    analyze(client, agent, ticket)

    call = fake_openai.chat_calls[0]
    system, user_message = call["messages"]
    assert "BILLING" in system["content"]
    assert "<ticket>" in user_message["content"]
    assert "I was double charged." in user_message["content"]
    schema = call["response_format"]["json_schema"]["schema"]
    assert "BILLING" in schema["properties"]["category"]["enum"]


def test_lowercase_codes_are_normalised(client, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    fake_openai.queue(chat_response(analysis_json(category="billing", priority="low")))

    response = analyze(client, agent, ticket)

    assert response.status_code == 200
    assert response.json()["category"] == "BILLING"


def test_malformed_json_is_rejected(client, db, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    fake_openai.queue(chat_response("Sure! The category is BILLING."))

    response = analyze(client, agent, ticket)

    assert response.status_code == 502
    db.refresh(ticket)
    assert ticket.category is None
    assert ticket.ai_summary is None


def test_invalid_values_are_rejected(client, db, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    fake_openai.queue(
        chat_response(analysis_json(priority="CRITICAL")),
        chat_response(analysis_json(category="SPACESHIPS")),
        chat_response(analysis_json(summary="")),
        chat_response(None),
    )

    for _ in range(4):
        assert analyze(client, agent, ticket).status_code == 502

    db.refresh(ticket)
    assert ticket.priority.value == "MEDIUM"


def test_timeout_returns_ai_error(client, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    fake_openai.queue(timeout_error())

    response = analyze(client, agent, ticket)

    assert response.status_code == 502
    assert response.json()["code"] == "ai_error"
    assert "timed out" in response.json()["detail"]


def test_usage_is_recorded_even_when_output_is_invalid(
    client, db, fake_openai, agent, customer, make_ticket
):
    ticket = make_ticket(customer)
    fake_openai.queue(chat_response("not json", prompt_tokens=80, completion_tokens=5))

    analyze(client, agent, ticket)

    usage = db.query(AIUsage).one()
    assert usage.operation == AIOperation.CLASSIFICATION
    assert usage.user_id == agent.id
    assert usage.ticket_id == ticket.id
    assert usage.model == "gpt-4o-mini-test"
    assert (usage.input_tokens, usage.output_tokens) == (80, 5)


def test_missing_token_counts_are_stored_as_null(
    client, db, fake_openai, agent, customer, make_ticket
):
    ticket = make_ticket(customer)
    response = chat_response(analysis_json())
    response.usage = None
    fake_openai.queue(response)

    analyze(client, agent, ticket)

    usage = db.query(AIUsage).one()
    assert usage.input_tokens is None
    assert usage.output_tokens is None


def test_ai_unavailable_without_api_key(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    response = analyze(client, agent, ticket)

    assert response.status_code == 503
    assert response.json()["code"] == "ai_unavailable"


def test_ai_can_be_turned_off_by_admin(client, fake_openai, admin, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    client.patch("/api/admin/settings", headers=auth_headers(admin), json={"ai_enabled": False})

    assert analyze(client, agent, ticket).status_code == 503
    status = client.get("/api/ai/status", headers=auth_headers(agent)).json()
    assert status["available"] is False


def test_customers_cannot_use_ai(client, fake_openai, customer, make_ticket):
    ticket = make_ticket(customer)

    assert analyze(client, customer, ticket).status_code == 403


def test_ai_requests_are_rate_limited(
    client, fake_openai, agent, customer, make_ticket, monkeypatch
):
    monkeypatch.setattr(ai_rate_limiter, "limit", 2)
    ticket = make_ticket(customer)
    fake_openai.queue(chat_response(analysis_json()), chat_response(analysis_json()))

    assert analyze(client, agent, ticket).status_code == 200
    assert analyze(client, agent, ticket).status_code == 200
    assert analyze(client, agent, ticket).status_code == 429


def test_new_ticket_is_analysed_in_background(client, db, fake_openai, customer):
    fake_openai.queue(chat_response(analysis_json(category="BILLING", priority="HIGH")))

    response = client.post(
        "/api/tickets",
        headers=auth_headers(customer),
        json={"subject": "Charged twice", "description": "My card was charged two times."},
    )

    assert response.status_code == 201
    ticket_id = response.json()["id"]
    usage = db.query(AIUsage).one()
    assert usage.user_id is None
    assert usage.ticket_id == ticket_id

    ticket = db.get(Ticket, ticket_id)
    assert ticket.category == "BILLING"
    assert ticket.priority.value == "HIGH"


def test_ticket_creation_succeeds_when_ai_fails(client, db, fake_openai, customer, agent):
    fake_openai.queue(timeout_error())

    response = client.post(
        "/api/tickets",
        headers=auth_headers(customer),
        json={"subject": "Export broken", "description": "The CSV export is empty."},
    )

    assert response.status_code == 201
    ticket = client.get(f"/api/tickets/{response.json()['id']}", headers=auth_headers(agent)).json()
    assert ticket["ai_summary"] is None
    assert ticket["category"] is None


def test_ticket_creation_succeeds_with_invalid_ai_output(client, fake_openai, customer):
    fake_openai.queue(chat_response("{broken"))

    response = client.post(
        "/api/tickets",
        headers=auth_headers(customer),
        json={"subject": "Export broken", "description": "The CSV export is empty."},
    )

    assert response.status_code == 201


def test_ticket_creation_without_ai_configured(client, db, customer):
    response = client.post(
        "/api/tickets",
        headers=auth_headers(customer),
        json={"subject": "Export broken", "description": "The CSV export is empty."},
    )

    assert response.status_code == 201
    assert db.query(AIUsage).count() == 0


def test_auto_analysis_can_be_disabled(client, db, fake_openai, admin, customer):
    client.patch(
        "/api/admin/settings", headers=auth_headers(admin), json={"auto_analyze_tickets": False}
    )

    client.post(
        "/api/tickets",
        headers=auth_headers(customer),
        json={"subject": "Export broken", "description": "The CSV export is empty."},
    )

    assert fake_openai.chat_calls == []


def test_summarize_conversation(client, db, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    client.post(
        f"/api/tickets/{ticket.id}/messages",
        headers=auth_headers(agent),
        json={"message": "Please try a private window."},
    )
    client.post(
        f"/api/tickets/{ticket.id}/messages",
        headers=auth_headers(customer),
        json={"message": "Tried it, same error."},
    )
    fake_openai.queue(chat_response("  Customer cannot log in; a private window did not help.  "))

    response = client.post(f"/api/ai/tickets/{ticket.id}/summarize", headers=auth_headers(agent))

    assert response.status_code == 200
    assert response.json()["summary"] == "Customer cannot log in; a private window did not help."
    conversation = fake_openai.chat_calls[0]["messages"][1]["content"]
    assert "Agent (Alex Agent):\nPlease try a private window." in conversation
    assert "Customer (Jane Customer):\nTried it, same error." in conversation
    db.refresh(ticket)
    assert ticket.ai_summary == "Customer cannot log in; a private window did not help."
    assert db.query(AIUsage).one().operation == AIOperation.SUMMARY


def test_empty_summary_is_an_error(client, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    fake_openai.queue(chat_response("   "))

    response = client.post(f"/api/ai/tickets/{ticket.id}/summarize", headers=auth_headers(agent))

    assert response.status_code == 502
