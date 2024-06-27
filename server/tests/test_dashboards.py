from datetime import UTC, datetime, timedelta

from app.models import TicketPriority, TicketStatus
from tests.conftest import auth_headers


def test_customer_stats_only_count_own_tickets(client, customer, other_customer, make_ticket):
    make_ticket(customer, status=TicketStatus.OPEN)
    make_ticket(customer, status=TicketStatus.WAITING_FOR_CUSTOMER)
    make_ticket(other_customer, status=TicketStatus.OPEN)

    stats = client.get("/api/tickets/stats", headers=auth_headers(customer)).json()

    assert stats["by_status"]["OPEN"] == 1
    assert stats["by_status"]["WAITING_FOR_CUSTOMER"] == 1
    assert stats["by_status"]["CLOSED"] == 0
    assert stats["assigned_to_me"] == 0


def test_agent_stats(client, agent, customer, make_ticket):
    make_ticket(customer, assigned_agent_id=agent.id)
    make_ticket(customer, assigned_agent_id=agent.id, status=TicketStatus.RESOLVED)
    make_ticket(customer, priority=TicketPriority.URGENT)
    make_ticket(customer, priority=TicketPriority.URGENT, status=TicketStatus.CLOSED)

    stats = client.get("/api/tickets/stats", headers=auth_headers(agent)).json()

    assert stats["assigned_to_me"] == 1
    assert stats["unassigned"] == 1
    assert stats["urgent"] == 1
    assert sum(stats["by_status"].values()) == 4


def test_admin_analytics(client, admin, customer, make_ticket):
    now = datetime.now(UTC)
    make_ticket(customer, category="BILLING", priority=TicketPriority.HIGH)
    make_ticket(customer, category="BILLING")
    make_ticket(
        customer,
        status=TicketStatus.RESOLVED,
        created_at=now - timedelta(hours=10),
        resolved_at=now - timedelta(hours=6),
    )
    make_ticket(
        customer,
        status=TicketStatus.CLOSED,
        created_at=now - timedelta(hours=8),
        resolved_at=now - timedelta(hours=6),
    )

    body = client.get("/api/admin/analytics", headers=auth_headers(admin)).json()

    assert body["total_tickets"] == 4
    assert body["open_tickets"] == 2
    assert body["resolved_tickets"] == 2
    assert body["average_resolution_hours"] == 3.0
    assert {"category": "BILLING", "count": 2} in body["by_category"]
    assert {"category": None, "count": 2} in body["by_category"]
    assert {"priority": "HIGH", "count": 1} in body["by_priority"]
    assert len(body["created_last_14_days"]) == 14
    assert sum(day["count"] for day in body["created_last_14_days"]) == 4


def test_analytics_with_no_tickets(client, admin):
    body = client.get("/api/admin/analytics", headers=auth_headers(admin)).json()

    assert body["total_tickets"] == 0
    assert body["average_resolution_hours"] is None


def test_analytics_is_admin_only(client, agent):
    assert client.get("/api/admin/analytics", headers=auth_headers(agent)).status_code == 403
