# A1 — Deadline Calculator

## Status

Implemented in `backend/services/deadline_calculator.py` with focused pytest
coverage in `backend/services/test_deadline.py`.

## Contract

- `DeadlineResult` frozen dataclass:
  - `deadline_date`
  - `days_remaining`
  - `urgency_level`
  - `court_type`
  - `response_window_days`
- `calculate_deadline(filing_date, court_type, service_date=None)`

## Rules

- Justice Court: 14 days from service date.
- District/County Court: next Monday after 20 days from service date.
- Missing service date: estimate service as filing date plus 3 days.
- Urgency:
  - `CRITICAL`: 3 days or fewer
  - `URGENT`: 4 to 7 days
  - `WARNING`: 8 to 14 days
  - `MONITOR`: more than 14 days

## Notes

- Accepts `date`, `datetime`, and ISO date strings.
- Normalizes common court labels such as `JP`, `Justice Court Precinct 1`,
  `District Court`, and `County Court at Law`.
- These calculations are legal information for alert triage, not legal advice.

## Verification

Run:

```bash
python3 -m pytest backend/services/test_deadline.py -q
```
