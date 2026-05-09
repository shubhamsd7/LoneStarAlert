"""Texas consumer debt statute of limitations triage.

These checks provide legal information for alert prioritization, not legal
advice. Texas consumer debt limitations are treated as four years for the demo
workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


DefenseStrength = Literal["STRONG", "BORDERLINE", "UNLIKELY", "NONE"]
CONSUMER_DEBT_LIMITATIONS_YEARS = 4.0
DAYS_PER_YEAR = 365.25


@dataclass(frozen=True)
class LimitationsResult:
    is_time_barred: bool
    defense_strength: DefenseStrength
    elapsed_years: float
    clock_start_date: date
    limitations_years: float
    debt_type: str


def check_statute_of_limitations(
    debt_origin_date: date | datetime | str,
    debt_type: str = "consumer_debt",
    last_payment_date: date | datetime | str | None = None,
    as_of_date: date | datetime | str | None = None,
) -> LimitationsResult:
    """Check Texas consumer debt limitations exposure.

    The limitations clock starts at last payment when available, otherwise at
    debt origin. `as_of_date` is injectable so tests and demos stay stable.
    """
    parsed_origin_date = _parse_required_date(debt_origin_date, "debt_origin_date")
    parsed_last_payment_date = _parse_optional_date(last_payment_date)
    parsed_as_of_date = _parse_optional_date(as_of_date) or date.today()
    clock_start_date = parsed_last_payment_date or parsed_origin_date

    elapsed_years = max(
        0.0,
        (parsed_as_of_date - clock_start_date).days / DAYS_PER_YEAR,
    )
    defense_strength = _classify_defense_strength(elapsed_years)

    return LimitationsResult(
        is_time_barred=elapsed_years > CONSUMER_DEBT_LIMITATIONS_YEARS,
        defense_strength=defense_strength,
        elapsed_years=elapsed_years,
        clock_start_date=clock_start_date,
        limitations_years=CONSUMER_DEBT_LIMITATIONS_YEARS,
        debt_type=_normalize_debt_type(debt_type),
    )


def _classify_defense_strength(elapsed_years: float) -> DefenseStrength:
    if elapsed_years > 4.0:
        return "STRONG"
    if elapsed_years > 3.5:
        return "BORDERLINE"
    if elapsed_years > 3.0:
        return "UNLIKELY"
    return "NONE"


def _normalize_debt_type(debt_type: str) -> str:
    text = str(debt_type or "").strip().lower().replace(" ", "_")
    return text or "consumer_debt"


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
