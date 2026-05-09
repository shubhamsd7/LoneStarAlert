"""Texas civil response deadline calculation service.

Implements the contract for Texas Justice Court and District/County Court
response deadlines per CPRC §16.051 and TRCP 21.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal


@dataclass
class DeadlineResult:
    """Result of deadline calculation with urgency assessment."""
    
    deadline_date: date
    """The absolute response deadline (non-extendable in most cases)."""
    
    days_remaining: int
    """Days from today until deadline. Negative if past deadline."""
    
    urgency_level: Literal["CRITICAL", "URGENT", "WARNING", "MONITOR"]
    """Urgency classification:
    - CRITICAL: <=3 days remaining
    - URGENT: <=7 days remaining
    - WARNING: <=14 days remaining
    - MONITOR: >14 days remaining
    """
    
    court_type: str
    """'justice' (JP court) or 'district' (District/County court)."""
    
    response_window_days: int
    """Total response window: 14 for JP, 20 for District."""


def calculate_deadline(
    filing_date: date | str,
    court_type: str,
    service_date: date | str | None = None,
) -> DeadlineResult:
    """Calculate Texas civil response deadline.
    
    Args:
        filing_date: Date case was filed (ISO format string or date object)
        court_type: 'justice' for JP court, 'district'/'county' for District Court
        service_date: Date defendant was served (ISO format string or date object)
                     If None, defaults to filing_date + 3 days (conservative)
    
    Returns:
        DeadlineResult with deadline_date, days_remaining, and urgency_level
    
    Rules:
        - Justice Court (JP): 14 days from service_date
        - District/County: next Monday after 20 days from service_date
        - If service_date is None: use filing_date + 3 days as estimate
    
    Raises:
        ValueError: If dates cannot be parsed or court_type is invalid
    """
    # Parse and validate inputs
    filing_dt = _parse_date(filing_date)
    service_dt = _parse_date(service_date) if service_date else None
    normalized_court_type = court_type.lower().strip()
    
    if not filing_dt:
        raise ValueError(f"Invalid filing_date: {filing_date}")
    
    if normalized_court_type not in ("justice", "district", "county"):
        raise ValueError(
            f"court_type must be 'justice' or 'district'/'county', got: {court_type}"
        )
    
    # If service_date not provided, estimate as filing_date + 3 days
    start_date = service_dt or (filing_dt + timedelta(days=3))
    
    # Calculate deadline based on court type
    if normalized_court_type == "justice":
        response_window_days = 14
        deadline_date = start_date + timedelta(days=14)
    else:  # district or county
        response_window_days = 20
        deadline_date = _following_monday(start_date + timedelta(days=20))
    
    # Calculate days remaining
    days_remaining = (deadline_date - date.today()).days
    
    # Determine urgency
    urgency_level = _calculate_urgency(days_remaining)
    
    return DeadlineResult(
        deadline_date=deadline_date,
        days_remaining=days_remaining,
        urgency_level=urgency_level,
        court_type=normalized_court_type,
        response_window_days=response_window_days,
    )


def _parse_date(value: date | str | None) -> date | None:
    """Parse date from multiple formats.
    
    Args:
        value: date object, ISO format string, or None
    
    Returns:
        Parsed date or None if input is None/empty
    
    Raises:
        ValueError: If string cannot be parsed as date
    """
    if isinstance(value, date):
        return value
    
    if not value:
        return None
    
    value_str = str(value).strip()
    if not value_str:
        return None
    
    try:
        # Handle ISO format with timezone
        parsed = datetime.fromisoformat(value_str.replace("Z", "+00:00"))
        return parsed.date()
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Cannot parse date: {value}") from e


def _following_monday(value: date) -> date:
    """Get the next Monday on or after the given date.
    
    If value is already a Monday, returns value.
    Otherwise returns the next Monday.
    
    Args:
        value: date to find next Monday for
    
    Returns:
        The same date if it's Monday, else the next Monday
    """
    weekday = value.weekday()  # 0=Monday, 6=Sunday
    if weekday == 0:  # Already Monday
        return value
    days_until_monday = 7 - weekday
    return value + timedelta(days=days_until_monday)


def _calculate_urgency(days_remaining: int) -> Literal["CRITICAL", "URGENT", "WARNING", "MONITOR"]:
    """Classify urgency based on days remaining.
    
    Args:
        days_remaining: Number of days until deadline
    
    Returns:
        Urgency level classification
    """
    if days_remaining <= 3:
        return "CRITICAL"
    elif days_remaining <= 7:
        return "URGENT"
    elif days_remaining <= 14:
        return "WARNING"
    else:
        return "MONITOR"
