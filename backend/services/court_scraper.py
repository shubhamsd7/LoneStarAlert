"""Court filing data access service.

The scraper is intentionally fail-closed: callers get an empty list if the
public court portal changes shape, rate limits us, or returns malformed data.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


HARRIS_API_BASE_URL = "https://odysseypafiledc.tylertech.cloud/harris/api/"
TRAVIS_PUBLIC_SEARCH_BASE_URL = "https://travis.tx.publicsearch.us/"
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 20


async def search_cases_by_name(name: str, county: str = "harris") -> list[dict]:
    """Search recent civil cases by defendant name."""
    return await _search_cases(query=name, county=county, search_type="name")


async def search_cases_by_address(address: str, county: str = "harris") -> list[dict]:
    """Search recent civil cases by property address."""
    return await _search_cases(query=address, county=county, search_type="address")


async def _search_cases(query: str, county: str, search_type: str) -> list[dict]:
    try:
        county_config = _county_config(county)
        if not query.strip() or county_config is None:
            return []

        payload = _build_search_payload(
            query=query,
            search_type=search_type,
            county=county_config["county"],
        )

        import httpx

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            for endpoint in county_config["endpoints"]:
                response = await _post_with_backoff(client, endpoint, payload)
                if response is None:
                    continue

                cases = _extract_case_records(
                    response,
                    source_name=county_config["source_name"],
                    source_url=county_config["source_url"],
                )
                if cases:
                    return cases
    except Exception:
        return []

    return []


def _county_config(county: str) -> dict[str, Any] | None:
    normalized_county = county.strip().lower()
    if normalized_county == "harris":
        return {
            "county": "harris",
            "source_name": "Harris County Odyssey Portal",
            "source_url": HARRIS_API_BASE_URL,
            "endpoints": [
                HARRIS_API_BASE_URL,
                f"{HARRIS_API_BASE_URL}search",
                f"{HARRIS_API_BASE_URL}cases/search",
                f"{HARRIS_API_BASE_URL}CaseSearch/Search",
            ],
        }

    if normalized_county == "travis":
        return {
            "county": "travis",
            "source_name": "Travis County Public Search",
            "source_url": TRAVIS_PUBLIC_SEARCH_BASE_URL,
            "endpoints": [
                TRAVIS_PUBLIC_SEARCH_BASE_URL,
                f"{TRAVIS_PUBLIC_SEARCH_BASE_URL}api/",
                f"{TRAVIS_PUBLIC_SEARCH_BASE_URL}api/search",
                f"{TRAVIS_PUBLIC_SEARCH_BASE_URL}api/cases/search",
            ],
        }

    return None


def _build_search_payload(query: str, search_type: str, county: str) -> dict[str, Any]:
    today = date.today()
    start_date = today - timedelta(days=90)
    clean_query = query.strip()

    payload: dict[str, Any] = {
        "county": county,
        "caseType": "civil",
        "filingDateFrom": start_date.isoformat(),
        "filingDateTo": today.isoformat(),
        "includePartyInformation": True,
    }

    if search_type == "address":
        payload.update(
            {
                "address": clean_query,
                "propertyAddress": clean_query,
                "searchText": clean_query,
            }
        )
    else:
        payload.update(
            {
                "defendantName": clean_query,
                "partyName": clean_query,
                "searchText": clean_query,
            }
        )

    return payload


async def _post_with_backoff(
    client: Any, endpoint: str, payload: dict[str, Any]
) -> Any | None:
    delay_seconds = 1.0

    for attempt in range(MAX_RETRIES):
        try:
            response = await client.post(endpoint, json=payload)

            if response.status_code == 429 and attempt < MAX_RETRIES - 1:
                await asyncio.sleep(delay_seconds)
                delay_seconds *= 2
                continue

            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt >= MAX_RETRIES - 1:
                return None

            await asyncio.sleep(delay_seconds)
            delay_seconds *= 2

    return None


def _extract_case_records(
    response_data: Any,
    source_name: str = "Unknown public court records source",
    source_url: str = "",
) -> list[dict]:
    raw_cases = _find_case_items(response_data)
    recent_cutoff = date.today() - timedelta(days=90)
    cases: list[dict] = []

    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            continue

        filing_date = _parse_date(
            _pick(
                raw_case,
                "filing_date",
                "filingDate",
                "filedDate",
                "dateFiled",
                "fileDate",
            )
        )
        if filing_date is None or filing_date < recent_cutoff:
            continue

        if not _is_civil_case(raw_case):
            continue

        cases.append(
            {
                "case_number": _pick(
                    raw_case,
                    "case_number",
                    "caseNumber",
                    "caseId",
                    "caseNbr",
                    "causeNumber",
                ),
                "plaintiff": _party_name(raw_case, "plaintiff"),
                "defendant": _party_name(raw_case, "defendant"),
                "filing_date": filing_date.isoformat(),
                "court_type": _court_type(raw_case),
                "case_type": _pick(
                    raw_case,
                    "case_type",
                    "caseType",
                    "caseCategory",
                    "type",
                    "caseStyle",
                )
                or "Civil",
                "amount_claimed": _amount_claimed(raw_case),
                "source_name": source_name,
                "source_url": source_url,
            }
        )

    return cases


def _find_case_items(response_data: Any) -> list[Any]:
    if isinstance(response_data, list):
        return response_data

    if not isinstance(response_data, dict):
        return []

    for key in ("cases", "items", "results", "data", "caseResults", "records"):
        value = response_data.get(key)
        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            nested = _find_case_items(value)
            if nested:
                return nested

    return []


def _is_civil_case(raw_case: dict[str, Any]) -> bool:
    text = " ".join(
        str(value)
        for value in (
            _pick(raw_case, "case_type", "caseType", "caseCategory", "type"),
            _pick(raw_case, "category", "division", "courtType", "caseStyle"),
        )
        if value
    ).lower()

    return not text or "civil" in text or "debt" in text or "contract" in text


def _court_type(raw_case: dict[str, Any]) -> str:
    text = " ".join(
        str(value)
        for value in (
            _pick(raw_case, "court_type", "courtType", "courtName", "court"),
            _pick(raw_case, "location", "division"),
        )
        if value
    ).lower()

    if "justice" in text or "jp" in text or "precinct" in text:
        return "justice"

    return "district"


def _party_name(raw_case: dict[str, Any], role: str) -> str | None:
    direct_name = _pick(raw_case, role, role.title(), f"{role}Name", f"{role}_name")
    if direct_name:
        return str(direct_name)

    parties = raw_case.get("parties") or raw_case.get("partyInformation")
    if not isinstance(parties, list):
        return None

    for party in parties:
        if not isinstance(party, dict):
            continue

        party_role = str(_pick(party, "role", "partyType", "type") or "").lower()
        if role in party_role:
            name = _pick(party, "name", "fullName", "businessName", "partyName")
            return str(name) if name else None

    return None


def _amount_claimed(raw_case: dict[str, Any]) -> str | None:
    value = _pick(
        raw_case,
        "amount_claimed",
        "amountClaimed",
        "claim_amount",
        "claimAmount",
        "amount",
        "damages",
    )
    if value in (None, ""):
        return None

    try:
        return str(Decimal(str(value).replace("$", "").replace(",", "").strip()))
    except (InvalidOperation, AttributeError):
        return str(value)


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if not value:
        return None

    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def _pick(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in source:
            return source[key]

    return None


async def main() -> None:
    cases = await search_cases_by_name("John Smith", county="harris")
    print(cases[0] if cases else "No cases found")


if __name__ == "__main__":
    asyncio.run(main())
