"""Texas legal aid lookup service."""

from __future__ import annotations


def find_legal_aid(zip_code: str) -> list[dict[str, str]]:
    """Return bounded Texas legal aid resources near a ZIP code."""
    prefix = "".join(character for character in str(zip_code) if character.isdigit())[:3]

    if prefix in {"770", "775", "776", "777"}:
        return [
            {
                "name": "Lone Star Legal Aid",
                "phone": "800-733-8394",
                "url": "https://www.lonestarlegal.org/",
            },
            {
                "name": "Houston Volunteer Lawyers",
                "phone": "713-228-0735",
                "url": "https://www.makejusticehappen.org/",
            },
        ]

    if prefix in {"733", "786", "787"}:
        return [
            {
                "name": "Texas RioGrande Legal Aid",
                "phone": "888-988-9996",
                "url": "https://www.trla.org/",
            },
            {
                "name": "Volunteer Legal Services of Central Texas",
                "phone": "512-476-5550",
                "url": "https://www.vlsoct.org/",
            },
        ]

    return [
        {
            "name": "TexasLawHelp.org",
            "phone": "Online resource",
            "url": "https://texaslawhelp.org/",
        },
        {
            "name": "Legal Aid Directory",
            "phone": "Call 2-1-1",
            "url": "https://www.txcourts.gov/programs-services/legal-aid/",
        },
    ]
