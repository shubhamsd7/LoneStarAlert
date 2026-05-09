"""Texas public property record lookup service."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode

try:
    import httpx
except ModuleNotFoundError:
    class _MissingHttpx:
        class AsyncClient:
            def __init__(self, *args, **kwargs) -> None:
                raise RuntimeError("httpx is not installed")

    httpx = _MissingHttpx()


TCAD_SEARCH_URL = "https://stage.traviscad.org/api/v1/search"
SUPPORTED_COUNTIES = {"travis"}
LOOKUP_TIMEOUT_SECONDS = 8.0

ADDRESS_ABBREVIATIONS = {
    "avenue": "AVE",
    "ave": "AVE",
    "boulevard": "BLVD",
    "blvd": "BLVD",
    "circle": "CIR",
    "cir": "CIR",
    "court": "CT",
    "ct": "CT",
    "drive": "DR",
    "dr": "DR",
    "highway": "HWY",
    "hwy": "HWY",
    "lane": "LN",
    "ln": "LN",
    "parkway": "PKWY",
    "pkwy": "PKWY",
    "place": "PL",
    "pl": "PL",
    "road": "RD",
    "rd": "RD",
    "street": "ST",
    "st": "ST",
    "terrace": "TER",
    "ter": "TER",
    "trail": "TRL",
    "trl": "TRL",
    "way": "WAY",
}

UNIT_MARKERS = {"apt", "apartment", "unit", "ste", "suite", "#"}


def normalize_address(raw_address: str) -> str:
    """Normalize a user-entered street address for public property search."""
    text = str(raw_address or "").strip().upper()
    if not text:
        return ""

    text = re.sub(r"[.,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = _remove_unit(tokens=text.split())

    normalized_tokens = [
        ADDRESS_ABBREVIATIONS.get(token.lower(), token) for token in tokens
    ]
    return " ".join(normalized_tokens)


async def lookup_owner(address: str, county: str = "travis") -> dict | None:
    """Look up Travis County property owner details from TCAD.

    Returns None for unsupported counties, empty results, network failures, or
    unexpected response shapes. The monitoring cycle should not crash because a
    public property data lookup is temporarily unavailable.
    """
    normalized_address = normalize_address(address)
    if not normalized_address or county.strip().lower() not in SUPPORTED_COUNTIES:
        return None

    url = f"{TCAD_SEARCH_URL}?{urlencode({'address': normalized_address})}"

    try:
        async with httpx.AsyncClient(timeout=LOOKUP_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None

    return _parse_tcad_owner(payload)


def _remove_unit(tokens: list[str]) -> list[str]:
    cleaned: list[str] = []
    index = 0

    while index < len(tokens):
        token = tokens[index].strip()
        marker = token.lower().removesuffix(".")

        if marker in UNIT_MARKERS:
            break

        if token.startswith("#"):
            break

        cleaned.append(token)
        index += 1

    return cleaned


def _parse_tcad_owner(payload: Any) -> dict | None:
    record = _first_record(payload)
    if not record:
        return None

    owner_name = _first_text(
        record,
        "owner_name",
        "ownerName",
        "owner",
        "owner_name_1",
        "owner1",
        "name",
    )
    parcel_id = _first_text(
        record,
        "parcel_id",
        "parcelId",
        "account",
        "account_number",
        "accountNumber",
        "prop_id",
        "property_id",
    )
    legal_description = _first_text(
        record,
        "legal_description",
        "legalDescription",
        "legal",
        "description",
    )
    owner_mailing_address = _mailing_address(record)

    if not any([owner_name, owner_mailing_address, parcel_id, legal_description]):
        return None

    return {
        "owner_name": owner_name,
        "owner_mailing_address": owner_mailing_address,
        "parcel_id": parcel_id,
        "legal_description": legal_description,
    }


def _first_record(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, list):
        return _first_dict(payload)

    if not isinstance(payload, dict):
        return None

    for key in ("results", "data", "items", "properties", "accounts"):
        value = payload.get(key)
        if isinstance(value, list):
            return _first_dict(value)

        if isinstance(value, dict):
            nested = _first_record(value)
            if nested:
                return nested

    return payload


def _first_dict(values: list[Any]) -> dict[str, Any] | None:
    for value in values:
        if isinstance(value, dict):
            return value
    return None


def _first_text(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def _mailing_address(record: dict[str, Any]) -> str | None:
    direct = _first_text(
        record,
        "owner_mailing_address",
        "ownerMailingAddress",
        "mailing_address",
        "mailingAddress",
    )
    if direct:
        return direct

    parts = [
        _first_text(record, "mailing_address_line1", "mailingAddressLine1", "addr1"),
        _first_text(record, "mailing_address_line2", "mailingAddressLine2", "addr2"),
        _first_text(record, "mailing_city", "mailingCity", "city"),
        _first_text(record, "mailing_state", "mailingState", "state"),
        _first_text(record, "mailing_zip", "mailingZip", "zip"),
    ]
    mailing_address = " ".join(part for part in parts if part)
    return mailing_address or None
