from __future__ import annotations

import asyncio

import pytest

from backend.services import property_lookup
from backend.services.property_lookup import lookup_owner, normalize_address


@pytest.mark.parametrize(
    ("raw_address", "normalized"),
    [
        (" 123 main street, Apt 4 ", "123 MAIN ST"),
        ("500 East Riverside Drive", "500 EAST RIVERSIDE DR"),
        ("742 evergreen terrace #12", "742 EVERGREEN TER"),
        ("", ""),
    ],
)
def test_normalize_address(raw_address: str, normalized: str) -> None:
    assert normalize_address(raw_address) == normalized


def test_lookup_owner_parses_mocked_tcad_results(monkeypatch) -> None:
    captured_urls = []

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "results": [
                    {
                        "ownerName": "Jane Smith",
                        "mailingAddress": "PO BOX 123 AUSTIN TX 78701",
                        "accountNumber": "10-1234-5678",
                        "legalDescription": "LOT 1 BLK A DEMO SUBDIVISION",
                    }
                ]
            }

    class MockAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> MockResponse:
            captured_urls.append(url)
            return MockResponse()

    monkeypatch.setattr(property_lookup.httpx, "AsyncClient", MockAsyncClient)

    result = asyncio.run(lookup_owner("123 Main Street Apt 4"))

    assert result == {
        "owner_name": "Jane Smith",
        "owner_mailing_address": "PO BOX 123 AUSTIN TX 78701",
        "parcel_id": "10-1234-5678",
        "legal_description": "LOT 1 BLK A DEMO SUBDIVISION",
    }
    assert captured_urls == [
        "https://stage.traviscad.org/api/v1/search?address=123+MAIN+ST"
    ]


def test_lookup_owner_returns_none_for_empty_results(monkeypatch) -> None:
    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"results": []}

    class MockAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> MockResponse:
            return MockResponse()

    monkeypatch.setattr(property_lookup.httpx, "AsyncClient", MockAsyncClient)

    assert asyncio.run(lookup_owner("123 Main St")) is None


def test_lookup_owner_returns_none_for_unavailable_api(monkeypatch) -> None:
    class MockAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str):
            raise TimeoutError("TCAD unavailable")

    monkeypatch.setattr(property_lookup.httpx, "AsyncClient", MockAsyncClient)

    assert asyncio.run(lookup_owner("123 Main St")) is None


def test_lookup_owner_returns_none_for_unsupported_county() -> None:
    assert asyncio.run(lookup_owner("123 Main St", county="harris")) is None
