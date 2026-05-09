"""Deadline estimates for Texas civil court alerts.

These calculations are legal information for TxAlert triage, not legal advice.
When service information is missing, the service date is estimated from filing
date so the monitor can still produce a conservative dashboard signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal


UrgencyLevel = Literal["CRITICAL", "URGENT", "WARNING", "MONITOR"]
CourtType = Literal["justice", "district", "county"]


@dataclass(frozen=True)
class DeadlineResult:
    deadline_date: date
    days_remaining: int
    urgency_level: UrgencyLevel
    court_type: CourtType
    response_window_days: int


def calculate_deadline(
    filing_date: date | datetime | str,
    court_type: str,
    service_date: date | datetime | str | None = None,
) -> DeadlineResult:
    """Calculate the response deadline and urgency for a Texas civil case."""
    parsed_filing_date = _parse_required_date(filing_date, "filing_date")
    normalized_court_type = _normalize_court_type(court_type)
    start_date = _parse_optional_date(service_date) or (
        parsed_filing_date + timedelta(days=3)
    )

    if normalized_court_type == "justice":
        response_window_days = 14
        deadline_date = start_date + timedelta(days=response_window_days)
    else:
        response_window_days = 20
        deadline_date = _next_monday_after(
            start_date + timedelta(days=response_window_days)
        )

    days_remaining = (deadline_date - date.today()).days

    return DeadlineResult(
        deadline_date=deadline_date,
        days_remaining=days_remaining,
        urgency_level=_calculate_urgency(days_remaining),
        court_type=normalized_court_type,
        response_window_days=response_window_days,
    )


def _parse_required_date(value: date | datetime | str, field_name: str) -> date:
    parsed = _parse_optional_date(value)
    if parsed is None:
        raise ValueError(f"{field_name} is required")
    return parsed


def _parse_optional_date(value: date | datetime | str | None) -> date | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise ValueError(f"Cannot parse date: {value}") from exc


def _normalize_court_type(court_type: str) -> CourtType:
    text = str(court_type or "").strip().lower()

    if text in {"justice", "jp", "j.p.", "justice court"} or "justice" in text:
        return "justice"

    if text in {"district", "district court"} or "district" in text:
        return "district"

    if text in {"county", "county court"} or "county" in text:
        return "county"

    raise ValueError(
        "court_type must be justice, district, or county; "
        f"got: {court_type!r}"
    )


def _next_monday_after(value: date) -> date:
    days_until_monday = (7 - value.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return value + timedelta(days=days_until_monday)


def _calculate_urgency(days_remaining: int) -> UrgencyLevel:
    if days_remaining <= 3:
        return "CRITICAL"
    if days_remaining <= 7:
        return "URGENT"
    if days_remaining <= 14:
        return "WARNING"
    return "MONITOR"
