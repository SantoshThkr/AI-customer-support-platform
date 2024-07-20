from app.dependencies.ai import ai_rate_limiter
from app.models import AIOperation, AIUsage, KnowledgeChunk
from tests.conftest import auth_headers
from tests.fakes import timeout_error
from tests.test_knowledge import PASSWORD_GUIDE, upload

BILLING_FAQ = b"""# Billing FAQ

## Duplicate charges

If a card was charged twice, the second charge is usually a pending authorization.

## Refunds

Annual plans can get a prorated refund within 30 days of renewal.
"""


def search(client, user, query, limit=3):
    return client.get(
        "/api/knowledge/search", params={"q": query, "limit": limit}, headers=auth_headers(user)
    ).json()


def test_upload_generates_embeddings(client, db, fake_openai, admin):
    response = upload(client, admin, "guide.md", PASSWORD_GUIDE)

    assert response.status_code == 201
    # The background task has run by the time TestClient returns.
    document = client.get(
        f"/api/knowledge/documents/{response.json()['id']}", headers=auth_headers(admin)
    ).json()
    assert document["status"] == "READY"
    assert document["embedded_chunk_count"] == document["chunk_count"] == 3

    chunks = db.query(KnowledgeChunk).all()
    assert all(len(chunk.embedding) == 1536 for chunk in chunks)
    assert fake_openai.embedding_calls[0]["dimensions"] == 1536


def test_embedding_usage_is_recorded_without_output_tokens(client, db, fake_openai, admin):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)

    usage = db.query(AIUsage).one()
    assert usage.operation == AIOperation.EMBEDDING
    assert usage.input_tokens > 0
    assert usage.output_tokens is None


def test_semantic_search_returns_most_similar_chunk(client, fake_openai, admin, agent):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)
    upload(client, admin, "billing.md", BILLING_FAQ)

    body = search(client, agent, "customer was charged twice on their card")

    assert body["mode"] == "semantic"
    assert body["results"][0]["section"] == "Duplicate charges"
    assert body["results"][0]["document_title"] == "Billing FAQ"
    scores = [result["score"] for result in body["results"]]
    assert scores == sorted(scores, reverse=True)


def test_semantic_search_records_query_embedding_usage(client, db, fake_openai, admin, agent):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)

    search(client, agent, "reset link expired")

    query_usage = db.query(AIUsage).filter_by(user_id=agent.id).one()
    assert query_usage.operation == AIOperation.EMBEDDING


def test_search_falls_back_to_keywords_without_ai(client, admin, agent):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)

    body = search(client, agent, "reset link")

    assert body["mode"] == "keyword"
    assert body["results"]


def test_search_falls_back_to_keywords_when_embedding_fails(client, fake_openai, admin, agent):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)
    fake_openai.embedding_error = timeout_error()

    body = search(client, agent, "reset link")

    assert body["mode"] == "keyword"
    assert body["results"][0]["section"] == "Reset link"


def test_search_uses_keywords_once_rate_limited(client, fake_openai, admin, agent, monkeypatch):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)
    monkeypatch.setattr(ai_rate_limiter, "limit", 1)

    assert search(client, agent, "reset link")["mode"] == "semantic"
    assert search(client, agent, "reset link")["mode"] == "keyword"


def test_failed_embedding_marks_document(client, db, fake_openai, admin, agent):
    fake_openai.embedding_error = timeout_error()

    created = upload(client, admin, "guide.md", PASSWORD_GUIDE).json()

    document = client.get(
        f"/api/knowledge/documents/{created['id']}", headers=auth_headers(admin)
    ).json()
    assert document["status"] == "FAILED"
    assert "Keyword search still works" in document["error_message"]
    assert document["embedded_chunk_count"] == 0
    assert search(client, agent, "reset link")["results"]


def test_regenerate_embeddings(client, fake_openai, admin):
    fake_openai.embedding_error = timeout_error()
    created = upload(client, admin, "guide.md", PASSWORD_GUIDE).json()
    fake_openai.embedding_error = None

    response = client.post(
        f"/api/knowledge/documents/{created['id']}/embed", headers=auth_headers(admin)
    )

    assert response.status_code == 200
    document = client.get(
        f"/api/knowledge/documents/{created['id']}", headers=auth_headers(admin)
    ).json()
    assert document["status"] == "READY"
    assert document["embedded_chunk_count"] == 3


def test_regenerate_embeddings_requires_ai(client, admin):
    created = upload(client, admin, "guide.md", PASSWORD_GUIDE).json()

    response = client.post(
        f"/api/knowledge/documents/{created['id']}/embed", headers=auth_headers(admin)
    )

    assert response.status_code == 503


def test_document_is_ready_without_embeddings_when_ai_is_off(client, admin):
    created = upload(client, admin, "guide.md", PASSWORD_GUIDE).json()

    assert created["status"] == "READY"
    assert created["embedded_chunk_count"] == 0
