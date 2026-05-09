"""Debt collector historical scoring service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Literal


ThreatLevel = Literal["HIGH", "MEDIUM", "LOW"]

IMPROPER_SERVICE_ERROR = "improper_service"
ROUND_AMOUNT_ERROR = "suspicious_round_amounts"
CLUSTERED_FILING_ERROR = "clustered_filing_dates"


@dataclass(frozen=True)
class CollectorProfile:
    plaintiff_name: str
    total_cases: int
    default_win_rate: float
    avg_claim_amount: float
    common_errors: list[str]
    threat_level: ThreatLevel


def score_collector(
    plaintiff_name: str,
    historical_cases: list[dict[str, Any]],
) -> CollectorProfile:
    """Score a collector from bounded historical case records."""
    matching_cases = [
        case for case in historical_cases if _matches_plaintiff(plaintiff_name, case)
    ]
    if not matching_cases and historical_cases:
        matching_cases = historical_cases

    total_cases = len(matching_cases)
    default_win_rate = _calculate_default_win_rate(matching_cases)
    avg_claim_amount = _calculate_avg_claim_amount(matching_cases)
    common_errors = _detect_common_errors(matching_cases)
    threat_level = _calculate_threat_level(
        total_cases=total_cases,
        default_win_rate=default_win_rate,
        avg_claim_amount=avg_claim_amount,
        common_errors=common_errors,
    )

    return CollectorProfile(
        plaintiff_name=plaintiff_name.strip(),
        total_cases=total_cases,
        default_win_rate=default_win_rate,
        avg_claim_amount=avg_claim_amount,
        common_errors=common_errors,
        threat_level=threat_level,
    )


def _matches_plaintiff(plaintiff_name: str, case: dict[str, Any]) -> bool:
    expected = _normalize_text(plaintiff_name)
    if not expected:
        return True

    actual = _normalize_text(case.get("plaintiff") or case.get("plaintiff_name"))
    return not actual or actual == expected


def _calculate_default_win_rate(cases: list[dict[str, Any]]) -> float:
    if not cases:
        return 0.0

    default_wins = sum(1 for case in cases if _is_default_win(case))
    return default_wins / len(cases)


def _is_default_win(case: dict[str, Any]) -> bool:
    fields = (
        case.get("outcome"),
        case.get("status"),
        case.get("disposition"),
        case.get("judgment_type"),
        case.get("judgment"),
        case.get("notes"),
    )
    text = " ".join(str(value).lower() for value in fields if value)
    return "default" in text and any(
        marker in text for marker in ("judgment", "win", "granted", "awarded")
    )


def _calculate_avg_claim_amount(cases: list[dict[str, Any]]) -> float:
    amounts = [
        amount
        for amount in (_parse_amount(case) for case in cases)
        if amount is not None
    ]
    if not amounts:
        return 0.0

    average = sum(amounts, Decimal("0")) / Decimal(len(amounts))
    return float(round(average, 2))


def _parse_amount(case: dict[str, Any]) -> Decimal | None:
    value = (
        case.get("amount_claimed")
        or case.get("claim_amount")
        or case.get("amount")
        or case.get("damages")
    )
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value).replace("$", "").replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None


def _detect_common_errors(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []

    if _improper_service_rate(cases) > 0.10:
        errors.append(IMPROPER_SERVICE_ERROR)

    if _has_suspicious_round_amounts(cases):
        errors.append(ROUND_AMOUNT_ERROR)

    if _has_clustered_filing_dates(cases):
        errors.append(CLUSTERED_FILING_ERROR)

    return errors


def _improper_service_rate(cases: list[dict[str, Any]]) -> float:
    if not cases:
        return 0.0

    flagged = sum(1 for case in cases if "improper service" in _case_notes(case))
    return flagged / len(cases)


def _case_notes(case: dict[str, Any]) -> str:
    fields = (
        case.get("notes"),
        case.get("case_notes"),
        case.get("defense_notes"),
        case.get("service_notes"),
    )
    return " ".join(str(value).lower() for value in fields if value)


def _has_suspicious_round_amounts(cases: list[dict[str, Any]]) -> bool:
    amounts = [
        amount
        for amount in (_parse_amount(case) for case in cases)
        if amount is not None and amount > 0
    ]
    if len(amounts) < 3:
        return False

    round_amounts = [
        amount
        for amount in amounts
        if amount == amount.quantize(Decimal("1"))
        and amount % Decimal("100") == 0
    ]
    return len(round_amounts) / len(amounts) >= 0.50


def _has_clustered_filing_dates(cases: list[dict[str, Any]]) -> bool:
    filing_dates = sorted(
        parsed
        for parsed in (_parse_date(case.get("filing_date")) for case in cases)
        if parsed is not None
    )
    if len(filing_dates) < 3:
        return False

    for index, filing_date in enumerate(filing_dates):
        window_end = filing_date + timedelta(days=7)
        filings_in_window = sum(
            1 for candidate in filing_dates[index:] if candidate <= window_end
        )
        if filings_in_window >= 3:
            return True

    return False


def _calculate_threat_level(
    total_cases: int,
    default_win_rate: float,
    avg_claim_amount: float,
    common_errors: list[str],
) -> ThreatLevel:
    score = 0

    if total_cases >= 25:
        score += 2
    elif total_cases >= 10:
        score += 1

    if default_win_rate >= 0.70:
        score += 2
    elif default_win_rate >= 0.40:
        score += 1

    if avg_claim_amount >= 5000:
        score += 1

    score += min(len(common_errors), 2)

    if score >= 4:
        return "HIGH"
    if score >= 2:
        return "MEDIUM"
    return "LOW"


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").lower().split())
