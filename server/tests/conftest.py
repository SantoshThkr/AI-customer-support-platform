import os

from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://support:support@localhost:5432/support_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, insert, select, text  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Ticket, User, UserRole  # noqa: E402
from app.services.security import create_access_token, hash_password  # noqa: E402

# Rows inserted by migrations (e.g. default categories) are restored after every truncate.
SEEDED_TABLES = ("categories",)
seeded_rows: dict[str, list[dict]] = {}

PASSWORD = "password123"
# Hashing once keeps the suite fast; bcrypt is intentionally slow.
PASSWORD_HASH = hash_password(PASSWORD)


def _recreate_test_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def database():
    _recreate_test_database()
    config = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    config.set_main_option(
        "script_location", os.path.join(os.path.dirname(__file__), "..", "alembic")
    )
    command.upgrade(config, "head")

    with engine.connect() as conn:
        for name in SEEDED_TABLES:
            table = Base.metadata.tables[name]
            rows = conn.execute(select(table).order_by(table.c.id)).mappings().all()
            seeded_rows[name] = [{k: v for k, v in row.items() if k != "id"} for row in rows]
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(database):
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
        for name, rows in seeded_rows.items():
            if rows:
                conn.execute(insert(Base.metadata.tables[name]), rows)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def make_user(db):
    counter = {"n": 0}

    def _make_user(role: UserRole = UserRole.CUSTOMER, **fields) -> User:
        counter["n"] += 1
        user = User(
            email=fields.pop("email", f"{role.value.lower()}{counter['n']}@example.com"),
            name=fields.pop("name", f"{role.value.title()} {counter['n']}"),
            password_hash=PASSWORD_HASH,
            role=role,
            **fields,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make_user


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


@pytest.fixture
def customer(make_user):
    return make_user(UserRole.CUSTOMER, name="Jane Customer")


@pytest.fixture
def other_customer(make_user):
    return make_user(UserRole.CUSTOMER, name="Other Customer")


@pytest.fixture
def agent(make_user):
    return make_user(UserRole.AGENT, name="Alex Agent")


@pytest.fixture
def admin(make_user):
    return make_user(UserRole.ADMIN, name="Ada Admin")


@pytest.fixture
def make_ticket(db):
    def _make_ticket(customer: User, **fields) -> Ticket:
        ticket = Ticket(
            customer_id=customer.id,
            subject=fields.pop("subject", "Cannot log in"),
            description=fields.pop("description", "I get an error every time I try to sign in."),
            **fields,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    return _make_ticket
