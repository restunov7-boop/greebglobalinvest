# GlobalGreenInvest Primary Test Checklist

## A. Environment

- `DATABASE_URL` is set for the intended test database.
- Database check passes:

```powershell
.\scripts\check_globalgreeninvest_database.ps1
```

- Migrations are applied only when intentionally requested.
- GlobalGreenInvest seed/check passes for the selected database.
- Frontend points to the correct backend:
  - `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`
  - `VITE_PROJECT_SLUG=global-green-invest`
  - `VITE_DEV_TELEGRAM_MOCK=true` for local test mode
- Telegram environment is reviewed:
  - `TELEGRAM_SENDER_MODE`
  - `TELEGRAM_REAL_SEND_SCOPE`
  - bot token presence
  - pilot target presence

## B. Member Flow

- `/app` loads.
- `/app/products` loads.
- Open a product without access.
- Create a purchase request.
- Confirm the product page shows request status.
- Confirm locked materials remain locked before admin grant.

## C. Admin Flow

- `/admin/users` opens.
- `/admin/requests` opens.
- Request list shows member request.
- Admin can set status to `Связались`.
- Admin can approve and grant product access.
- `/admin/products` and `/admin/insights` still work.

## D. Product Access Flow

- After approve-and-grant, member can open locked product materials.
- Creating a request does not auto-grant access.
- Approve-and-grant can be repeated without duplicate access rows.

## E. Telegram Pilot Flow

- `/admin/settings` shows sender status.
- Real mode is only used with `pilot` scope first.
- Dry-run is reviewed before processing.
- Process pending once.
- Only the pilot recipient receives the message.

## F. Still Not Production

- No real payments.
- No Telegram payments.
- No CSV import.
- No automated renewals.
- No background workers.
- No production monitoring/alerts.
- Legal text and final policies still need product review.
