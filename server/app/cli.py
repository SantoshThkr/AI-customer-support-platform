"""Small management commands.

python -m app.cli create-user --email admin@example.com --name "Admin" --role ADMIN
python -m app.cli import-knowledge sample_data/knowledge
python -m app.cli seed-demo
"""

import argparse
import getpass
import sys
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select

from app.database import SessionLocal
from app.models import KnowledgeDocument, UserRole
from app.services import knowledge as knowledge_service
from app.services.users import create_user


def create_user_command(args: argparse.Namespace) -> int:
    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            user = create_user(
                db, email=args.email, name=args.name, password=password, role=UserRole(args.role)
            )
        except HTTPException as exc:
            print(exc.detail, file=sys.stderr)
            return 1
    print(f"Created {user.role.value} {user.email} (id={user.id})")
    return 0


def import_knowledge_command(args: argparse.Namespace) -> int:
    folder = Path(args.folder)
    files = sorted(
        path for path in folder.iterdir() if path.suffix.lower() in knowledge_service.FILE_TYPES
    )
    if not files:
        print(f"No .txt, .md or .pdf files found in {folder}", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        existing = set(db.scalars(select(KnowledgeDocument.filename)).all())
        for path in files:
            if path.name in existing:
                print(f"skip   {path.name} (already imported)")
                continue
            try:
                with path.open("rb") as file_obj:
                    file_type, text = knowledge_service.read_upload(file_obj, path.name)
                document = knowledge_service.create_document(
                    db,
                    title=knowledge_service.default_title(path.name, text),
                    text=text,
                    file_type=file_type,
                    filename=path.name,
                    uploaded_by=None,
                )
            except HTTPException as exc:
                print(f"error  {path.name}: {exc.detail}", file=sys.stderr)
                continue
            print(f"added  {path.name} ({document.chunk_count} chunks)")
    return 0


DEMO_USERS = [
    ("admin@example.com", "Ada Admin", UserRole.ADMIN),
    ("agent@example.com", "Alex Agent", UserRole.AGENT),
    ("customer@example.com", "John Carter", UserRole.CUSTOMER),
]


def seed_demo_command(args: argparse.Namespace) -> int:
    """Create one account per role and load the sample articles. For local use only."""
    with SessionLocal() as db:
        for email, name, role in DEMO_USERS:
            try:
                create_user(db, email=email, name=name, password=args.password, role=role)
                print(f"Created {role.value.lower()} {email}")
            except HTTPException:
                print(f"skip   {email} (already exists)")

    sample_folder = Path(__file__).resolve().parent.parent / "sample_data" / "knowledge"
    import_knowledge_command(argparse.Namespace(folder=str(sample_folder)))
    print(f"\nDemo password for all accounts: {args.password}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subcommands = parser.add_subparsers(dest="command", required=True)

    create = subcommands.add_parser("create-user", help="Create a user with any role")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--role", choices=[role.value for role in UserRole], default="CUSTOMER")
    create.add_argument("--password", help="Prompted for when omitted")
    create.set_defaults(handler=create_user_command)

    importer = subcommands.add_parser(
        "import-knowledge", help="Add every .txt/.md/.pdf file in a folder to the knowledge base"
    )
    importer.add_argument("folder")
    importer.set_defaults(handler=import_knowledge_command)

    demo = subcommands.add_parser(
        "seed-demo", help="Create demo admin/agent/customer accounts and sample articles"
    )
    demo.add_argument("--password", default="password123")
    demo.set_defaults(handler=seed_demo_command)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
