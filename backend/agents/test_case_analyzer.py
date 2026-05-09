from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from backend.agents.case_analyzer import analyze_case
from backend.models.case import CourtCase


def _case(**overrides):
    values = {
        "id": "case-1",
        "watch_id": "watch-1",
        "case_number": "J1-CV-24-123456",
        "plaintiff": "LVNV Funding LLC",
        "defendant": "John Smith",
        "filing_date": date.today(),
        "court_type": "justice",
        "county": "harris",
        "case_type": "Debt Claim",
        "amount_claimed": Decimal("1200.00"),
        "deadline_date": date.today() + timedelta(days=2),
        "days_remaining": 2,
        "is_time_barred": True,
        "collector_win_rate": 0.91,
        "status": "active",
    }
    values.update(overrides)
    return CourtCase(**values)


def test_analyze_case_prioritizes_time_barred_and_urgency() -> None:
    analysis = analyze_case(_case())

    assert analysis["strongest_defense"].startswith("Statute of limitations")
    assert "Critical" in analysis["urgency_note"]
    assert any("Debt ownership proof" in item for item in analysis["defenses"])
    assert analysis["deterministic_signals"]["is_time_barred"] is True


def test_analyze_case_handles_missing_deadline_and_amount() -> None:
    analysis = analyze_case(
        _case(
            amount_claimed=None,
            deadline_date=None,
            days_remaining=None,
            is_time_barred=None,
            collector_win_rate=None,
        )
    )

    assert "Deadline not calculated" in analysis["urgency_note"]
    assert any("Amount dispute" in item for item in analysis["defenses"])
    assert "not legal advice" in analysis["plain_language_summary"]
