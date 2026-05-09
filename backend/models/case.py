from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class WatchEntry(BaseModel):
    id: str
    type: Literal["name", "address"]
    value: str
    county: str
    user_email: str
    created_at: datetime


class CourtCase(BaseModel):
    id: str
    watch_id: str
    case_number: str
    plaintiff: str
    defendant: str
    filing_date: date
    court_type: Literal["justice", "district"]
    county: str
    case_type: str
    amount_claimed: Decimal | None = None
    deadline_date: date | None = None
    days_remaining: int | None = None
    is_time_barred: bool | None = None
    collector_win_rate: float | None = Field(default=None, ge=0, le=1)
    status: Literal["active", "alerted", "resolved"]


class Alert(BaseModel):
    id: str
    case_id: str
    message: str
    answer_form_url: str | None = None
    legal_aid: list[dict[str, Any]] = Field(default_factory=list)
    sent_at: datetime
