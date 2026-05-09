"""Deterministic pattern detection for bounded court-history batches."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from backend.models.pattern import PatternSignal


def detect_patterns(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect simple filing patterns and return frontend-compatible payloads."""
    signals = [
        signal
        for signal in (
            _bulk_filing_day(cases),
            _repeat_plaintiff_window(cases),
            _zip_cluster(cases),
        )
        if signal is not None
    ]
    top_signal = _top_signal(signals)

    return {
        "patterns": [signal.model_dump() for signal in signals],
        "pattern": _frontend_signal(top_signal),
        "pattern_description": top_signal.description if top_signal else None,
        "pattern_severity": top_signal.severity if top_signal else None,
        "anomaly_score": top_signal.anomaly_score if top_signal else None,
    }


def _bulk_filing_day(cases: list[dict[str, Any]]) -> PatternSignal | None:
    filing_dates = [
        parsed for parsed in (_parse_date(case.get("filing_date")) for case in cases)
        if parsed is not None
    ]
    if len(filing_dates) < 3:
        return None

    filing_counts = Counter(filing_dates)
    filing_date, count = filing_counts.most_common(1)[0]
    if count < 3:
        return None

    severity = _severity(count, high=8, medium=5)
    return PatternSignal(
        type="bulk_filing_day",
        severity=severity,
        description=f"{count} cases were filed on {filing_date.isoformat()}.",
        anomaly_score=_score(count, high=10),
        matching_cases=count,
    )


def _repeat_plaintiff_window(cases: list[dict[str, Any]]) -> PatternSignal | None:
    by_plaintiff: dict[str, list[date]] = defaultdict(list)
    for case in cases:
        plaintiff = _normalize(case.get("plaintiff") or case.get("plaintiff_name"))
        filing_date = _parse_date(case.get("filing_date"))
        if plaintiff and filing_date:
            by_plaintiff[plaintiff].append(filing_date)

    best: tuple[str, int] | None = None
    for plaintiff, filing_dates in by_plaintiff.items():
        filing_dates.sort()
        for index, start_date in enumerate(filing_dates):
            end_date = start_date + timedelta(days=14)
            count = sum(1 for candidate in filing_dates[index:] if candidate <= end_date)
            if count >= 3 and (best is None or count > best[1]):
                best = (plaintiff, count)

    if best is None:
        return None

    plaintiff, count = best
    severity = _severity(count, high=10, medium=5)
    return PatternSignal(
        type="repeat_plaintiff",
        severity=severity,
        description=f"{plaintiff.title()} filed {count} cases within a short period.",
        anomaly_score=_score(count, high=12),
        matching_cases=count,
    )


def _zip_cluster(cases: list[dict[str, Any]]) -> PatternSignal | None:
    zip_codes = [
        zip_code for zip_code in (_extract_zip(case) for case in cases) if zip_code
    ]
    if len(zip_codes) < 3:
        return None

    zip_counts = Counter(zip_codes)
    zip_code, count = zip_counts.most_common(1)[0]
    if count < 3:
        return None

    severity = _severity(count, high=8, medium=5)
    return PatternSignal(
        type="zip_cluster",
        severity=severity,
        description=f"{count} cases cluster in ZIP {zip_code}.",
        anomaly_score=_score(count, high=10),
        matching_cases=count,
    )


def _top_signal(signals: list[PatternSignal]) -> PatternSignal | None:
    if not signals:
        return None
    return max(signals, key=lambda signal: signal.anomaly_score)


def _frontend_signal(signal: PatternSignal | None) -> dict[str, Any] | None:
    if signal is None:
        return None
    return {
        "severity": signal.severity,
        "description": signal.description,
        "anomalyScore": signal.anomaly_score,
    }


def _extract_zip(case: dict[str, Any]) -> str | None:
    for key in ("zip", "zip_code", "zipcode", "defendant_zip", "address_zip"):
        value = case.get(key)
        if value:
            digits = "".join(character for character in str(value) if character.isdigit())
            if len(digits) >= 5:
                return digits[:5]
    return None


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def _severity(count: int, high: int, medium: int) -> str:
    if count >= high:
        return "high"
    if count >= medium:
        return "medium"
    return "low"


def _score(count: int, high: int) -> float:
    return round(min(1.0, count / high), 2)
