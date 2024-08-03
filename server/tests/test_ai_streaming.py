from app.models import AIOperation, AIUsage, TicketMessage
from tests.conftest import auth_headers
from tests.fakes import parse_sse, stream_chunks, timeout_error
from tests.test_knowledge import PASSWORD_GUIDE, upload


def stream(client, user, ticket, path="suggest-response/stream", json=None):
    return client.post(
        f"/api/ai/tickets/{ticket.id}/{path}", headers=auth_headers(user), json=json or {}
    )


def test_streams_suggested_response(client, db, fake_openai, admin, agent, customer, make_ticket):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)
    ticket = make_ticket(customer, subject="Reset link expired")
    fake_openai.queue(stream_chunks(["Hi Jane,", " the link", " expires after 30 minutes."]))

    response = stream(client, agent, ticket)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    assert events[0][0] == "sources"
    assert events[0][1]["sources"][0]["document_title"] == "Password Reset Guide"
    deltas = [data["text"] for name, data in events if name == "delta"]
    assert "".join(deltas) == "Hi Jane, the link expires after 30 minutes."
    assert events[-1] == ("done", {})

    call = fake_openai.chat_calls[-1]
    assert call["stream"] is True
    assert db.query(TicketMessage).count() == 0


def test_stream_records_usage_from_final_chunk(
    client, db, fake_openai, agent, customer, make_ticket
):
    ticket = make_ticket(customer)
    fake_openai.queue(stream_chunks(["Hello"], prompt_tokens=321, completion_tokens=12))

    stream(client, agent, ticket)

    usage = db.query(AIUsage).filter_by(operation=AIOperation.SUGGESTED_RESPONSE).one()
    assert (usage.input_tokens, usage.output_tokens) == (321, 12)


def test_stream_error_midway_sends_error_event(
    client, db, fake_openai, agent, customer, make_ticket
):
    ticket = make_ticket(customer)
    fake_openai.queue(stream_chunks(["Hi", " there", " more"], fail_after=2))

    events = parse_sse(stream(client, agent, ticket).text)

    names = [name for name, _ in events]
    assert names == ["sources", "delta", "delta", "error"]
    usage = db.query(AIUsage).one()
    assert usage.input_tokens is None


def test_stream_that_cannot_start_returns_http_error(
    client, fake_openai, agent, customer, make_ticket
):
    ticket = make_ticket(customer)
    fake_openai.queue(timeout_error())

    response = stream(client, agent, ticket)

    assert response.status_code == 502


def test_stream_requires_ai(client, agent, customer, make_ticket):
    ticket = make_ticket(customer)

    assert stream(client, agent, ticket).status_code == 503


def test_customer_cannot_stream(client, fake_openai, customer, make_ticket):
    ticket = make_ticket(customer)

    assert stream(client, customer, ticket).status_code == 403


def test_streams_copilot_answer(client, db, fake_openai, agent, customer, make_ticket):
    ticket = make_ticket(customer)
    fake_openai.queue(stream_chunks(["Ask them ", "to try again."]))

    response = stream(
        client, agent, ticket, "copilot/stream", {"question": "What should I tell them?"}
    )

    events = parse_sse(response.text)
    assert "".join(data["text"] for name, data in events if name == "delta") == (
        "Ask them to try again."
    )
    assert db.query(AIUsage).one().operation == AIOperation.COPILOT
