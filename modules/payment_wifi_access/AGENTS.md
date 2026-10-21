# Payment WiFi Access Rules

## TDD Requirements

- Start every task with a failing test in `tests/test_wifi_access.py` or a new focused test file under `tests/`.
- Cover these invariants in tests:
  - A valid paid transaction generates WiFi credentials.
  - Each payment generates a unique username and password.
  - A `payment_id` can activate access only once.
  - Default access duration is 24 hours.
  - Unpaid or mismatched transactions are rejected.
  - Mock behavior matches RouterOS behavior at the service API level.

## Implementation Notes

- Keep payment validation in `service.py`.
- Keep credential generation in `password.py`.
- Keep RouterOS and mock adapters in `adapters.py`.
- Keep custom Hotspot page rendering in `pages.py`.
- Keep RouterOS login page generation in `build.py`.
- The Hotspot login page can be hosted directly by Mikrotik; use a separate web server such as nginx only when the portal must live outside RouterOS.
- Do not put transaction storage directly in adapters.
- For production, persist paid and activated transaction IDs in a database.

