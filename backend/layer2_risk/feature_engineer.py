"""Deterministic feature engineering for TxAlert risk scoring."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def build_case_features(case: Any) -> dict[str, Any]:
    """Extract stable numeric features from a case-like object or dict."""
    days_remaining = _to_int(_read(case, "days_remaining"))
    collector_win_rate = _clamp(_to_float(_read(case, "collector_win_rate")) or 0.0)
    is_time_barred = _to_bool(_read(case, "is_time_barred"))
    court_type = str(_read(case, "court_type") or "").lower()

    features = {
        "court_type": court_type,
        "is_justice_court": court_type == "justice",
        "collector_win_rate": collector_win_rate,
        "days_remaining": days_remaining,
        "deadline_pressure": _deadline_pressure(days_remaining),
        "is_time_barred": is_time_barred,
        "plaintiff_strength_adjustment": -0.25 if is_time_barred is True else 0.0,
        "alert_importance_boost": 0.20 if is_time_barred is True else 0.0,
        "amount_claimed": _to_float(_read(case, "amount_claimed")),
        "filing_date": _date_to_iso(_read(case, "filing_date")),
    }
    return features


def _deadline_pressure(days_remaining: int | None) -> float:
    if days_remaining is None:
        return 0.20
    if days_remaining <= 0:
        return 1.0
    if days_remaining <= 3:
        return 0.90
    if days_remaining <= 7:
        return 0.75
    if days_remaining <= 14:
        return 0.45
    return 0.15


def _read(source: Any, name: str) -> Any:
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _date_to_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value:
        return str(value)
    return None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
