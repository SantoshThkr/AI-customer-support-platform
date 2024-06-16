"""Small management commands.

python -m app.cli create-user --email admin@example.com --name "Admin" --role ADMIN
"""

import argparse
import getpass
import sys

from fastapi import HTTPException

from app.database import SessionLocal
from app.models import UserRole
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


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subcommands = parser.add_subparsers(dest="command", required=True)

    create = subcommands.add_parser("create-user", help="Create a user with any role")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--role", choices=[role.value for role in UserRole], default="CUSTOMER")
    create.add_argument("--password", help="Prompted for when omitted")
    create.set_defaults(handler=create_user_command)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
