# Render Backend Setup

## Service

- Type: Web Service
- Name: `globalgreeninvest-backend`
- Root directory: `backend`
- Environment: Python
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`render.yaml` contains the same safe service definition without secrets.

## Required Environment Variables

Set these in Render dashboard. Do not commit real values.

```env
APP_ENV=staging
APP_NAME=GlobalGreenInvest
DATABASE_URL=<Supabase session pooler URL>
JWT_SECRET=<strong random secret>
CORS_ORIGINS=https://YOUR_FRONTEND.vercel.app,http://127.0.0.1:5173,http://localhost:5173
DEV_AUTH_ENABLED=true
TELEGRAM_SENDER_MODE=mock
TELEGRAM_REAL_SEND_SCOPE=pilot
TELEGRAM_BOT_TOKEN=
TELEGRAM_PILOT_CHAT_ID=
```

For a real production launch, set:

```env
APP_ENV=production
DEV_AUTH_ENABLED=false
```

Keep `TELEGRAM_SENDER_MODE=mock` for the first cloud deploy. Switch to `real` only for a controlled pilot test.

## Migrations And Seed

Run from Render shell after the service is deployed and env vars are configured:

```bash
cd backend
python -m alembic upgrade head
python scripts/seed_globalgreeninvest_demo.py
python scripts/check_globalgreeninvest_demo.py
```

The seed is intended to be idempotent. It creates/updates known GlobalGreenInvest demo records and does not drop data.

## Smoke URLs

Replace the host with your Render URL:

```text
https://YOUR_BACKEND.onrender.com/api/v1/health
https://YOUR_BACKEND.onrender.com/api/v1/community/info
```
