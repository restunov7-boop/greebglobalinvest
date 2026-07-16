# GlobalGreenInvest Demo Runbook

## Preferred Launch

No Docker or Postgres is required for the local demo. The demo scripts set `DATABASE_URL` to the local SQLite database at `backend/local_dev.db`.

From the repo root:

```powershell
cd C:\Users\restu\Documents\core\core-community-app
.\scripts\start_globalgreeninvest_demo.ps1
```

Optional browser open:

```powershell
.\scripts\start_globalgreeninvest_demo.ps1 -OpenBrowser
```

Refresh demo data while servers are already running:

```powershell
.\scripts\reseed_globalgreeninvest_demo.ps1
```

Check demo readiness:

```powershell
.\scripts\check_globalgreeninvest_demo.ps1
```

Primary readiness, without changing data by default:

```powershell
.\scripts\check_globalgreeninvest_primary_readiness.ps1
```

## Manual No-Docker Fallback

Use these commands if you want to start backend and frontend yourself.

First prepare or refresh the SQLite demo database:

```powershell
.\scripts\reseed_globalgreeninvest_demo.ps1
```

Terminal 1:

```powershell
.\scripts\start_globalgreeninvest_backend_sqlite.ps1
```

Terminal 2:

```powershell
.\scripts\start_globalgreeninvest_frontend.ps1
```

Do not run raw uvicorn for the demo unless the demo environment variables are already set. A raw command like this may use the default Postgres URL and fail when Docker/Postgres is absent:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Stop helper, with confirmation:

```powershell
.\scripts\stop_globalgreeninvest_demo.ps1
```

## Local Setup

Use these manual steps if the one-command launcher is not suitable for your environment.

1. Go to backend:

```powershell
cd C:\Users\restu\Documents\core\core-community-app\backend
```

2. If the local database is not up to date, run migrations:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

3. Run demo seed:

```powershell
.\.venv\Scripts\python.exe scripts\seed_globalgreeninvest_demo.py
```

4. Run diagnostic:

```powershell
.\.venv\Scripts\python.exe scripts\check_globalgreeninvest_demo.py
```

5. Start backend using the current project dev command.

6. Start frontend using the current project dev command.

## Pages To Open

- `/app`
- `/app/products`
- `/app/settings`
- `/admin/products`
- `/admin/requests`
- `/admin/posts`
- `/admin/insights`

## Demo Walkthrough

- Dashboard
- Post and insight detail
- Useful reaction
- Exchanges
- Products catalog
- Product locked materials
- Product unlocked materials with access
- Admin product/material editing
- Product purchase request from member product page
- Admin request handling at `/admin/requests`
- Admin posts/insights editing
- Admin notification queue demo:
  - Open `/admin/insights`.
  - Create or edit an insight with `urgent` enabled and `published` status.
  - Open `/admin/settings`.
  - Use `Проверить без обработки` to preview pending notification processing.
  - Use `Обработать pending` to mark queued records as processed in safe demo mode.
  - Confirm the list shows `Mock-отправлено`, `Пропущено`, or `Ошибка`.

By default, notification processing uses mock/demo mode. It does not call Telegram, does not require a bot token, and does not send real messages.

## Telegram Sender Modes

Local demo defaults to mock mode:

```powershell
$env:TELEGRAM_SENDER_MODE="mock"
```

Real mode is intentionally opt-in:

```powershell
$env:TELEGRAM_SENDER_MODE="real"
$env:TELEGRAM_BOT_TOKEN="..."
```

Warnings:

- `mock` is the safe default and sends no real Telegram messages.
- `real` sends actual Telegram messages when an admin processes pending notifications.
- `real` mode requires `TELEGRAM_BOT_TOKEN`; without it, processing fails safely.
- Dry-run never sends real Telegram messages.
- Never commit or paste a real bot token into tracked files.
- Do not use real mode with demo users unless that is intentional.

### Telegram Real Pilot

Use pilot mode for the first real delivery test. It allows real Telegram sending only to one explicitly configured test recipient:

```powershell
$env:TELEGRAM_SENDER_MODE="real"
$env:TELEGRAM_BOT_TOKEN="..."
$env:TELEGRAM_REAL_SEND_SCOPE="pilot"
$env:TELEGRAM_PILOT_CHAT_ID="123456789"
```

Recommended pilot flow:

1. Configure only your test chat/user id.
2. Run dry-run from `/admin/settings`.
3. Confirm non-pilot recipients are skipped.
4. Process pending once.
5. Confirm only the pilot target received the message.

Pilot checklist before processing:

1. Restart backend after setting env variables.
2. Open `/admin/settings`.
3. Confirm checklist shows real mode.
4. Confirm token is configured.
5. Confirm scope is `pilot`.
6. Confirm pilot target is configured.
7. Confirm pending count.
8. Run dry-run.
9. Review dry-run result.
10. Process pending once.

Do not use this until you are intentionally ready for broad production sending:

```powershell
$env:TELEGRAM_REAL_SEND_SCOPE="all"
```

`all` sends real Telegram messages to every eligible pending recipient. Keep local demo and normal development in mock mode.

## Primary DB Test

Use this only for a production-like test database. Do not paste real credentials into tracked files.

```powershell
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME"
.\scripts\check_globalgreeninvest_database.ps1
```

To apply migrations and seed/check GlobalGreenInvest on the configured database:

```powershell
.\scripts\prepare_globalgreeninvest_primary_test.ps1
```

For non-interactive test runs:

```powershell
.\scripts\prepare_globalgreeninvest_primary_test.ps1 -Yes
```

The prepare script does not drop or delete data. It runs migrations, the idempotent GlobalGreenInvest seed, and the diagnostic check.

## Telegram Bot Diagnostics

Review safe Telegram sender environment:

```powershell
.\scripts\check_globalgreeninvest_telegram.ps1
```

Check bot token with Telegram `getMe` without sending messages:

```powershell
.\scripts\check_telegram_bot_token.ps1
```

The token is never printed by the helper scripts.

## Primary Test Checklist

Use the full checklist before a real DB/bot pilot:

```text
docs/globalgreeninvest_primary_test_checklist.md
```

## Not Implemented Yet

- Payments
- Telegram payments
- CSV import
- Real file upload/storage
- Full users/access admin UI
- Production deployment
