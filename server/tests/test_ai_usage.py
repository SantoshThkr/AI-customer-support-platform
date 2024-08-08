from datetime import UTC, datetime, timedelta

from app.models import AIOperation, AIUsage
from tests.conftest import auth_headers


def add_usage(db, operation, *, user=None, input_tokens=100, output_tokens=20, days_ago=0, **extra):
    usage = AIUsage(
        operation=operation,
        model=extra.pop("model", "gpt-4o-mini"),
        user_id=user.id if user else None,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        created_at=datetime.now(UTC) - timedelta(days=days_ago),
        **extra,
    )
    db.add(usage)
    db.commit()
    return usage


def test_usage_report_totals_and_breakdowns(client, db, admin, agent):
    add_usage(db, AIOperation.CLASSIFICATION, input_tokens=100, output_tokens=20)
    add_usage(db, AIOperation.SUGGESTED_RESPONSE, user=agent, input_tokens=500, output_tokens=150)
    add_usage(db, AIOperation.SUGGESTED_RESPONSE, user=agent, input_tokens=300, output_tokens=100)
    add_usage(
        db,
        AIOperation.EMBEDDING,
        user=agent,
        input_tokens=40,
        output_tokens=None,
        model="text-embedding-3-small",
    )
    add_usage(db, AIOperation.COPILOT, user=agent, input_tokens=None, output_tokens=None)
    add_usage(db, AIOperation.SUMMARY, user=agent, days_ago=45)

    report = client.get("/api/admin/ai-usage?days=30", headers=auth_headers(admin)).json()

    assert report["totals"] == {"requests": 5, "input_tokens": 940, "output_tokens": 270}
    assert report["requests_without_token_counts"] == 1
    by_operation = {row["operation"]: row for row in report["by_operation"]}
    assert by_operation["SUGGESTED_RESPONSE"]["requests"] == 2
    assert by_operation["SUGGESTED_RESPONSE"]["input_tokens"] == 800
    assert "SUMMARY" not in by_operation
    models = {row["model"]: row["requests"] for row in report["by_model"]}
    assert models == {"gpt-4o-mini": 4, "text-embedding-3-small": 1}
    assert report["top_users"][0] == {"user_id": agent.id, "name": agent.name, "requests": 4}
    assert {"user_id": None, "name": "Automatic (system)", "requests": 1} in report["top_users"]
    assert len(report["by_day"]) == 30
    assert sum(day["count"] for day in report["by_day"]) == 5
    assert report["recent"][0]["operation"] == "COPILOT"
    assert len(report["recent"]) == 6


def test_analytics_include_ai_request_count(client, db, admin):
    add_usage(db, AIOperation.CLASSIFICATION)
    add_usage(db, AIOperation.CLASSIFICATION, days_ago=40)

    body = client.get("/api/admin/analytics", headers=auth_headers(admin)).json()

    assert body["ai_requests_last_30_days"] == 1


def test_empty_usage_report(client, admin):
    report = client.get("/api/admin/ai-usage", headers=auth_headers(admin)).json()

    assert report["totals"] == {"requests": 0, "input_tokens": 0, "output_tokens": 0}
    assert report["recent"] == []


def test_usage_report_is_admin_only(client, agent):
    assert client.get("/api/admin/ai-usage", headers=auth_headers(agent)).status_code == 403
