"""Autonomous court monitoring agent.

This cycle helps legal aid organizations check public court records for their
clients, similar to a paralegal doing a bounded morning review.
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from supabase import Client, create_client

from backend.models.case import CourtCase, WatchEntry
from backend.services import court_scraper, deadline_calculator


MAX_WATCH_ENTRIES_PER_CYCLE = 10
COUNTY_QUERY_DELAY_SECONDS = 2
WATCH_ENTRIES_TABLE = "watch_entries"
COURT_CASES_TABLE = "court_cases"


supabase_client: Client | None = None


async def run_monitor_cycle() -> list[CourtCase]:
    """Run one bounded public-record monitoring cycle."""
    cycle_started_at = datetime.now(timezone.utc)
    print(f"[court_monitor] cycle started at {cycle_started_at.isoformat()}")

    new_cases: list[CourtCase] = []

    try:
        client = _get_supabase_client()
        watch_entries = _load_watch_entries(client)
        print(f"[court_monitor] loaded {len(watch_entries)} watch entries")
    except Exception as exc:
        print(f"[court_monitor] failed to load watch entries: {exc}")
        print(f"[court_monitor] cycle ended at {datetime.now(timezone.utc).isoformat()}")
        return []

    for watch_entry in watch_entries:
        print(
            "[court_monitor] checking "
            f"{watch_entry.type} watch {watch_entry.id} in {watch_entry.county}"
        )

        try:
            search_results = await _search_watch_entry(watch_entry)
            print(
                "[court_monitor] found "
                f"{len(search_results)} raw results for watch {watch_entry.id}"
            )

            for result in search_results:
                case_number = str(result.get("case_number") or "").strip()
                if not case_number:
                    print("[court_monitor] skipping result with no case number")
                    continue

                if _case_exists(client, case_number):
                    print(f"[court_monitor] skipping duplicate case {case_number}")
                    continue

                court_case = _build_court_case(watch_entry, result)
                _save_court_case(client, court_case)
                new_cases.append(court_case)
                print(f"[court_monitor] saved new case {court_case.case_number}")
        except Exception as exc:
            print(f"[court_monitor] watch {watch_entry.id} failed: {exc}")

        await asyncio.sleep(COUNTY_QUERY_DELAY_SECONDS)

    cycle_ended_at = datetime.now(timezone.utc)
    print(
        "[court_monitor] cycle ended at "
        f"{cycle_ended_at.isoformat()} with {len(new_cases)} new cases"
    )
    return new_cases


def _get_supabase_client() -> Client:
    global supabase_client

    if supabase_client is not None:
        return supabase_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    supabase_client = create_client(supabase_url, supabase_key)
    return supabase_client


def _load_watch_entries(client: Client) -> list[WatchEntry]:
    response = (
        client.table(WATCH_ENTRIES_TABLE)
        .select("*")
        .limit(MAX_WATCH_ENTRIES_PER_CYCLE)
        .execute()
    )

    return [WatchEntry.model_validate(item) for item in response.data or []]


async def _search_watch_entry(watch_entry: WatchEntry) -> list[dict]:
    if watch_entry.type == "address":
        return await court_scraper.search_cases_by_address(
            watch_entry.value, county=watch_entry.county
        )

    return await court_scraper.search_cases_by_name(
        watch_entry.value, county=watch_entry.county
    )


def _case_exists(client: Client, case_number: str) -> bool:
    response = (
        client.table(COURT_CASES_TABLE)
        .select("id")
        .eq("case_number", case_number)
        .limit(1)
        .execute()
    )

    return bool(response.data)


def _build_court_case(watch_entry: WatchEntry, result: dict[str, Any]) -> CourtCase:
    filing_date = _parse_date(result.get("filing_date")) or date.today()
    deadline = _calculate_deadline(filing_date, result.get("court_type"))

    return CourtCase(
        id=str(uuid4()),
        watch_id=watch_entry.id,
        case_number=str(result.get("case_number") or ""),
        plaintiff=str(result.get("plaintiff") or "Unknown plaintiff"),
        defendant=str(result.get("defendant") or watch_entry.value),
        filing_date=filing_date,
        court_type=_normalize_court_type(result.get("court_type")),
        county=watch_entry.county,
        case_type=str(result.get("case_type") or "Civil"),
        amount_claimed=_parse_decimal(result.get("amount_claimed")),
        deadline_date=deadline.get("deadline_date"),
        days_remaining=deadline.get("days_remaining"),
        status="active",
    )


def _calculate_deadline(filing_date: date, court_type: Any) -> dict[str, Any]:
    calculate_deadline = getattr(deadline_calculator, "calculate_deadline", None)
    if calculate_deadline is None:
        return {"deadline_date": None, "days_remaining": None}

    try:
        result = calculate_deadline(filing_date, _normalize_court_type(court_type))
    except Exception as exc:
        print(f"[court_monitor] deadline calculation failed: {exc}")
        return {"deadline_date": None, "days_remaining": None}

    if isinstance(result, dict):
        return {
            "deadline_date": _parse_date(result.get("deadline_date")),
            "days_remaining": result.get("days_remaining"),
        }

    return {
        "deadline_date": _parse_date(getattr(result, "deadline_date", None)),
        "days_remaining": getattr(result, "days_remaining", None),
    }


def _save_court_case(client: Client, court_case: CourtCase) -> None:
    client.table(COURT_CASES_TABLE).insert(
        court_case.model_dump(mode="json")
    ).execute()


def _normalize_court_type(value: Any) -> str:
    court_type = str(value or "").lower()
    if court_type == "justice" or "justice" in court_type or "jp" in court_type:
        return "justice"

    return "district"


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value

    if not value:
        return None

    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value).replace("$", "").replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None
