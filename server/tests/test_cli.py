import argparse

from app.cli import import_knowledge_command
from app.models import DocumentStatus, KnowledgeDocument


def test_import_knowledge_embeds_documents_when_ai_is_available(db, fake_openai, tmp_path, capsys):
    (tmp_path / "guide.md").write_text("# Guide\n\nReset links expire after 30 minutes.")
    (tmp_path / "notes.docx").write_bytes(b"ignored")

    assert import_knowledge_command(argparse.Namespace(folder=str(tmp_path))) == 0

    document = db.query(KnowledgeDocument).one()
    assert document.status == DocumentStatus.READY
    assert document.embedded_chunk_count == 1
    assert "added  guide.md (1 chunks, READY)" in capsys.readouterr().out


def test_import_knowledge_skips_existing_files(db, tmp_path, capsys):
    (tmp_path / "guide.md").write_text("# Guide\n\nSome text.")
    args = argparse.Namespace(folder=str(tmp_path))

    import_knowledge_command(args)
    import_knowledge_command(args)

    assert db.query(KnowledgeDocument).count() == 1
    assert "skip   guide.md" in capsys.readouterr().out
