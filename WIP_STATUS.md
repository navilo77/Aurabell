# WIP Status
Branch: auth-remediation-cookie
State: WIP — NOT production ready.

## Completed
- P-02: Cookie-based auth ✅
- P-16: Route group rename ✅
- P-17: Payment page build fix ✅
- P-21: Refresh cookie 7d ✅

## Known broken
- P-20: Cart returns 500 for logged-in users (get_current_user returns
  User model; cart/router.py still uses dict access). Fix in next session.

## Not started
- P-03: Offline queue wiring
- P-04: Server-side role guard
- P-18: no-img cleanup