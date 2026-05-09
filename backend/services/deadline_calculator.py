"""Texas civil response deadline calculation service."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


def calculate_deadline(
    filing_date: date | str,
    court_type: str,
    service_date: date | str | None = None,
) -> dict[str, Any]:
    """Calculate a basic Texas civil response deadline.

    If service date is unknown, use filing date as a conservative placeholder
    for the hackathon demo flow. A later iteration can replace this with
    service-event parsing from docket records.
    """
    start_date = _parse_date(service_date) or _parse_date(filing_date) or date.today()
    normalized_court_type = court_type.lower()

    if normalized_court_type == "justice":
        deadline_date = start_date + timedelta(days=14)
    else:
        deadline_date = _following_monday(start_date + timedelta(days=20))

    days_remaining = (deadline_date - date.today()).days
    return {
        "deadline_date": deadline_date,
        "days_remaining": days_remaining,
        "urgency_level": _urgency_level(days_remaining),
    }


def _following_monday(value: date) -> date:
    days_until_monday = (7 - value.weekday()) % 7
    return value + timedelta(days=days_until_monday)


def _urgency_level(days_remaining: int) -> str:
    if days_remaining < 3:
        return "CRITICAL"
    if days_remaining < 7:
        return "URGENT"
    if days_remaining < 14:
        return "WARNING"
    return "MONITOR"


def _parse_date(value: date | str | None) -> date | None:
    if isinstance(value, date):
        return value

    if not value:
        return None

    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
