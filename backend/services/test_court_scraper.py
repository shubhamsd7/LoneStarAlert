from __future__ import annotations

from datetime import date, timedelta

from backend.services.court_scraper import (
    HARRIS_API_BASE_URL,
    TRAVIS_PUBLIC_SEARCH_BASE_URL,
    _build_search_payload,
    _county_config,
    _extract_case_records,
)


def test_extract_case_records_returns_recent_civil_cases_with_source() -> None:
    response = {
        "cases": [
            {
                "caseNumber": "J1-CV-24-123456",
                "plaintiff": "LVNV Funding LLC",
                "defendant": "John Smith",
                "filingDate": date.today().isoformat(),
                "caseType": "Civil Debt Claim",
                "courtName": "Justice Court Precinct 1",
                "amountClaimed": "$1,234.50",
            },
            {
                "caseNumber": "OLD-CV-1",
                "plaintiff": "Old Collector",
                "defendant": "John Smith",
                "filingDate": (date.today() - timedelta(days=120)).isoformat(),
                "caseType": "Civil Debt Claim",
            },
        ]
    }

    cases = _extract_case_records(
        response,
        source_name="Harris County Odyssey Portal",
        source_url=HARRIS_API_BASE_URL,
    )

    assert len(cases) == 1
    assert cases[0]["case_number"] == "J1-CV-24-123456"
    assert cases[0]["plaintiff"] == "LVNV Funding LLC"
    assert cases[0]["defendant"] == "John Smith"
    assert cases[0]["court_type"] == "justice"
    assert cases[0]["amount_claimed"] == "1234.50"
    assert cases[0]["source_name"] == "Harris County Odyssey Portal"
    assert cases[0]["source_url"] == HARRIS_API_BASE_URL


def test_extract_case_records_handles_nested_party_information() -> None:
    response = {
        "data": {
            "items": [
                {
                    "causeNumber": "D-1-CV-24-999999",
                    "fileDate": date.today().isoformat(),
                    "caseCategory": "Civil",
                    "courtType": "District Court",
                    "partyInformation": [
                        {"partyType": "Plaintiff", "name": "Midland Credit"},
                        {"partyType": "Defendant", "fullName": "Jane Smith"},
                    ],
                    "claim_amount": "5000",
                }
            ]
        }
    }

    cases = _extract_case_records(
        response,
        source_name="Travis County Public Search",
        source_url=TRAVIS_PUBLIC_SEARCH_BASE_URL,
    )

    assert cases == [
        {
            "case_number": "D-1-CV-24-999999",
            "plaintiff": "Midland Credit",
            "defendant": "Jane Smith",
            "filing_date": date.today().isoformat(),
            "court_type": "district",
            "case_type": "Civil",
            "amount_claimed": "5000",
            "source_name": "Travis County Public Search",
            "source_url": TRAVIS_PUBLIC_SEARCH_BASE_URL,
        }
    ]


def test_county_config_routes_supported_counties_only() -> None:
    harris = _county_config("Harris")
    travis = _county_config("travis")

    assert harris is not None
    assert harris["source_name"] == "Harris County Odyssey Portal"
    assert travis is not None
    assert travis["source_url"] == TRAVIS_PUBLIC_SEARCH_BASE_URL
    assert _county_config("dallas") is None


def test_build_search_payload_for_name_and_address() -> None:
    name_payload = _build_search_payload("John Smith", "name", "harris")
    address_payload = _build_search_payload("123 Main St", "address", "travis")

    assert name_payload["defendantName"] == "John Smith"
    assert name_payload["partyName"] == "John Smith"
    assert name_payload["county"] == "harris"
    assert address_payload["propertyAddress"] == "123 Main St"
    assert address_payload["county"] == "travis"
