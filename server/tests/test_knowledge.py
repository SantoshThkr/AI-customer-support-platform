from app.config import settings
from app.models import KnowledgeChunk
from app.services.knowledge import clean_text, split_into_chunks
from tests.conftest import auth_headers

PASSWORD_GUIDE = b"""# Password Reset Guide

Customers can reset their password from the sign-in page.

## Reset link

Click "Forgot password" and enter the account email. The reset link expires after 30 minutes.

## Locked accounts

After five failed attempts the account is locked for 15 minutes.
"""


def make_pdf(text: str) -> bytes:
    """Build a minimal one-page PDF with a single line of text."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref_at = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    pdf += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref_at,
    )
    return pdf


def upload(client, user, filename, data, content_type="application/octet-stream", **form):
    return client.post(
        "/api/knowledge/documents",
        headers=auth_headers(user),
        files={"file": (filename, data, content_type)},
        data=form,
    )


def test_upload_markdown_document(client, db, admin):
    response = upload(client, admin, "password-reset-guide.md", PASSWORD_GUIDE, "text/markdown")

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Password Reset Guide"
    assert body["file_type"] == "MARKDOWN"
    assert body["status"] == "READY"
    assert body["chunk_count"] == 3

    chunks = db.query(KnowledgeChunk).order_by(KnowledgeChunk.chunk_index).all()
    assert [chunk.metadata_.get("section") for chunk in chunks] == [
        "Password Reset Guide",
        "Reset link",
        "Locked accounts",
    ]
    assert "expires after 30 minutes" in chunks[1].chunk_text


def test_title_falls_back_to_file_name(client, admin):
    response = upload(client, admin, "billing_faq-2024.txt", b"Refunds take 5 days.")

    assert response.json()["title"] == "Billing faq 2024"


def test_upload_text_document_with_custom_title(client, admin):
    response = upload(
        client, admin, "faq.txt", b"Refunds are issued within 5 days.", title="Billing FAQ"
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Billing FAQ"
    assert response.json()["file_type"] == "TXT"


def test_upload_pdf_extracts_text(client, admin):
    response = upload(
        client, admin, "setup.pdf", make_pdf("Install the desktop app first."), "application/pdf"
    )

    assert response.status_code == 201
    detail = client.get(
        f"/api/knowledge/documents/{response.json()['id']}", headers=auth_headers(admin)
    ).json()
    assert "Install the desktop app first." in detail["content"]


def test_create_document_from_text(client, admin):
    response = client.post(
        "/api/knowledge/documents",
        headers=auth_headers(admin),
        data={"title": "Cancellation policy", "content": "You can cancel any time from Billing."},
    )

    assert response.status_code == 201
    assert response.json()["filename"] is None


def test_unsupported_file_type(client, admin):
    response = upload(client, admin, "script.exe", b"MZ\x90\x00")

    assert response.status_code == 400


def test_pdf_extension_with_wrong_content(client, admin):
    response = upload(client, admin, "guide.pdf", b"just some text pretending to be a pdf")

    assert response.status_code == 400


def test_corrupt_pdf(client, admin):
    response = upload(client, admin, "broken.pdf", b"%PDF-1.4\nnot really a pdf")

    assert response.status_code == 400


def test_binary_text_file_is_rejected(client, admin):
    response = upload(client, admin, "notes.txt", b"\x00\x01\x02binary")

    assert response.status_code == 400


def test_non_utf8_text_file_is_rejected(client, admin):
    response = upload(client, admin, "notes.txt", "café".encode("latin-1"))

    assert response.status_code == 400


def test_empty_file_is_rejected(client, admin):
    assert upload(client, admin, "empty.md", b"").status_code == 400
    assert upload(client, admin, "blank.md", b"   \n\n  ").status_code == 400


def test_file_size_limit(client, admin, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)

    response = upload(client, admin, "big.txt", b"x" * 100)

    assert response.status_code == 413


def test_missing_file_and_content(client, admin):
    response = client.post(
        "/api/knowledge/documents", headers=auth_headers(admin), data={"title": "Only a title"}
    )

    assert response.status_code == 400


def test_only_admins_manage_documents(client, agent, customer, admin):
    assert upload(client, agent, "a.md", b"Agent doc").status_code == 403
    assert upload(client, customer, "a.md", b"Customer doc").status_code == 403

    created = upload(client, admin, "a.md", b"Admin doc").json()
    delete_url = f"/api/knowledge/documents/{created['id']}"
    assert client.delete(delete_url, headers=auth_headers(agent)).status_code == 403


def test_customers_cannot_read_knowledge_base(client, admin, customer):
    created = upload(client, admin, "internal.md", b"Internal refund rules").json()
    headers = auth_headers(customer)

    assert client.get("/api/knowledge/documents", headers=headers).status_code == 403
    assert (
        client.get(f"/api/knowledge/documents/{created['id']}", headers=headers).status_code == 403
    )
    assert client.get("/api/knowledge/search?q=refund", headers=headers).status_code == 403


def test_agents_can_list_and_read_documents(client, admin, agent):
    created = upload(client, admin, "guide.md", PASSWORD_GUIDE).json()

    listing = client.get("/api/knowledge/documents", headers=auth_headers(agent)).json()
    detail = client.get(
        f"/api/knowledge/documents/{created['id']}", headers=auth_headers(agent)
    ).json()

    assert [document["id"] for document in listing] == [created["id"]]
    assert listing[0]["chunk_count"] == 3
    assert detail["content"].startswith("# Password Reset Guide")


def test_delete_removes_chunks(client, db, admin):
    created = upload(client, admin, "guide.md", PASSWORD_GUIDE).json()

    response = client.delete(
        f"/api/knowledge/documents/{created['id']}", headers=auth_headers(admin)
    )

    assert response.status_code == 204
    assert db.query(KnowledgeChunk).count() == 0


def test_keyword_search(client, admin, agent):
    upload(client, admin, "guide.md", PASSWORD_GUIDE)
    upload(
        client, admin, "billing.md", b"# Billing\n\nInvoices are sent on the first of the month."
    )

    response = client.get(
        "/api/knowledge/search",
        params={"q": "how long is the reset link valid"},
        headers=auth_headers(agent),
    )

    body = response.json()
    assert body["mode"] == "keyword"
    assert body["results"][0]["section"] == "Reset link"
    assert body["results"][0]["document_title"] == "Password Reset Guide"


def test_clean_text():
    raw = "Title\r\n\r\n\r\n\r\nFirst   line  \twith spaces\r\nSecond line   \n\n\n\nEnd"

    assert clean_text(raw) == "Title\n\nFirst line with spaces\nSecond line\n\nEnd"


def test_chunks_respect_max_size():
    paragraph = "This sentence is about billing. " * 40
    text = "\n\n".join([paragraph.strip()] * 3)

    chunks = split_into_chunks(text, max_chars=300)

    assert len(chunks) > 3
    assert all(len(chunk.text) <= 300 for chunk in chunks)
    assert "".join(chunk.text for chunk in chunks).count("billing") == 120


def test_very_long_sentence_is_split_on_words():
    chunks = split_into_chunks("word " * 500, max_chars=200)

    assert all(len(chunk.text) <= 200 for chunk in chunks)
    assert sum(chunk.text.count("word") for chunk in chunks) == 500
