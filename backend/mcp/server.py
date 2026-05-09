"""TxAlert MCP server."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from backend.agents import court_monitor
from backend.models.case import WatchEntry
from backend.services.deadline_calculator import calculate_deadline
from backend.services.legal_aid_finder import find_legal_aid as find_legal_aid_service
from backend.services.limitations_checker import check_statute_of_limitations


load_dotenv()


try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - lets py_compile pass before dependency install

    class FastMCP:  # type: ignore[no-redef]
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.name = "TxAlert"

        def tool(self, *_args: Any, **_kwargs: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func

            return decorator

        def run(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("Install the 'mcp' package to run the MCP server")


WATCH_ENTRIES_TABLE = "watch_entries"
COURT_CASES_TABLE = "court_cases"
ALERTS_TABLE = "alerts"


def _create_mcp() -> FastMCP:
    try:
        return FastMCP("TxAlert", host="0.0.0.0", port=8001)
    except TypeError:
        return FastMCP("TxAlert")


mcp = _create_mcp()


@mcp.tool()
async def watch_name(name: str, county: str = "harris") -> dict[str, Any]:
    """Register a name to watch for civil court filings in Texas public records."""
    return await _register_watch("name", name, county)


@mcp.tool()
async def watch_address(address: str, county: str = "travis") -> dict[str, Any]:
    """Register a property address to watch for Texas public court actions."""
    return await _register_watch("address", address, county)


@mcp.tool()
def get_active_alerts(email: str) -> dict[str, Any]:
    """Get all active court case alerts for an email address."""
    try:
        client = court_monitor._get_supabase_client()
        watches = (
            client.table(WATCH_ENTRIES_TABLE)
            .select("*")
            .eq("user_email", email)
            .limit(25)
            .execute()
            .data
            or []
        )
        watch_ids = [watch["id"] for watch in watches if watch.get("id")]
        alerts: list[dict[str, Any]] = []

        for watch_id in watch_ids[:10]:
            cases = (
                client.table(COURT_CASES_TABLE)
                .select("*")
                .eq("watch_id", watch_id)
                .limit(25)
                .execute()
                .data
                or []
            )
            for court_case in cases:
                case_alerts = (
                    client.table(ALERTS_TABLE)
                    .select("*")
                    .eq("case_id", court_case.get("id"))
                    .limit(5)
                    .execute()
                    .data
                    or []
                )
                alerts.extend(case_alerts)

        return {"email": email, "alerts": alerts[:25], "count": len(alerts[:25])}
    except Exception as exc:
        return _error("get_active_alerts", exc)


@mcp.tool()
def get_case_deadline(case_number: str, county: str) -> dict[str, Any]:
    """Get days remaining before default judgment for a Texas civil case."""
    try:
        client = court_monitor._get_supabase_client()
        record = _load_case_by_number(client, case_number, county)
        if record is None:
            return {"case_number": case_number, "county": county, "found": False}

        if record.get("deadline_date") and record.get("days_remaining") is not None:
            return {
                "case_number": case_number,
                "county": county,
                "found": True,
                "deadline_date": record.get("deadline_date"),
                "days_remaining": record.get("days_remaining"),
            }

        result = calculate_deadline(
            record.get("filing_date"),
            record.get("court_type") or "justice",
        )
        return {
            "case_number": case_number,
            "county": county,
            "found": True,
            "deadline_date": result.deadline_date.isoformat(),
            "days_remaining": result.days_remaining,
            "urgency_level": result.urgency_level,
        }
    except Exception as exc:
        return _error("get_case_deadline", exc)


@mcp.tool()
def check_statute_limits(case_number: str, county: str) -> dict[str, Any]:
    """Check whether a Texas debt case may be past the four-year limitations window."""
    try:
        client = court_monitor._get_supabase_client()
        record = _load_case_by_number(client, case_number, county)
        if record is None:
            return {"case_number": case_number, "county": county, "found": False}

        if record.get("is_time_barred") is not None:
            return {
                "case_number": case_number,
                "county": county,
                "found": True,
                "is_time_barred": record.get("is_time_barred"),
                "source": "stored_case_analysis",
            }

        debt_date = (
            record.get("debt_origin_date")
            or record.get("debt_date")
            or record.get("last_payment_date")
        )
        if not debt_date:
            return {
                "case_number": case_number,
                "county": county,
                "found": True,
                "is_time_barred": None,
                "message": "No debt origin date is available in the stored record.",
            }

        result = check_statute_of_limitations(
            debt_date,
            record.get("debt_type") or "unknown",
            record.get("last_payment_date"),
        )
        return {
            "case_number": case_number,
            "county": county,
            "found": True,
            "is_time_barred": result.is_time_barred,
            "defense_strength": result.defense_strength,
            "elapsed_years": round(result.elapsed_years, 2),
        }
    except Exception as exc:
        return _error("check_statute_limits", exc)


@mcp.tool()
def find_legal_aid(zip_code: str) -> dict[str, Any]:
    """Find free legal aid organizations near a Texas ZIP code."""
    return {
        "zip_code": zip_code,
        "resources": find_legal_aid_service(zip_code),
        "note": "Call ahead to confirm eligibility and availability.",
    }


async def _register_watch(watch_type: str, value: str, county: str) -> dict[str, Any]:
    if not value.strip():
        return {"success": False, "error": "watch value is required"}

    try:
        client = court_monitor._get_supabase_client()
        watch_entry = WatchEntry(
            id=str(uuid4()),
            type=watch_type,  # type: ignore[arg-type]
            value=value.strip(),
            county=county.strip().lower(),
            user_email="mcp@txalert.local",
            created_at=datetime.now(timezone.utc),
        )
        client.table(WATCH_ENTRIES_TABLE).insert(
            {**watch_entry.model_dump(mode="json"), "status": "active"}
        ).execute()

        search_results = await court_monitor._search_watch_entry(watch_entry)
        return {
            "success": True,
            "watch_id": watch_entry.id,
            "type": watch_type,
            "value": value,
            "county": county,
            "first_check_results": len(search_results),
            "message": "Watch registered using bounded public-record lookup.",
        }
    except Exception as exc:
        return _error("register_watch", exc)


def _load_case_by_number(client: Any, case_number: str, county: str) -> dict[str, Any] | None:
    response = (
        client.table(COURT_CASES_TABLE)
        .select("*")
        .eq("case_number", case_number)
        .eq("county", county.strip().lower())
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return response.data[0]


def _error(tool_name: str, exc: Exception) -> dict[str, Any]:
    return {"success": False, "tool": tool_name, "error": str(exc)}


if __name__ == "__main__":
    try:
        mcp.run(transport="sse")
    except TypeError:
        mcp.run()
