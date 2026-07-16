# GlobalGreenInvest Cloud Deployment Runbook

Target architecture:

- Database: Supabase PostgreSQL via Session pooler
- Backend: Render Web Service
- Frontend: Vercel Vite static app
- Telegram: backend-only env, mock first, pilot later

No real secrets belong in Git.

## 1. Supabase

Use the Supabase Session pooler `DATABASE_URL`.

Do not use the direct IPv6-only database host if your local/provider environment has IPv6 connectivity issues.

From your local PowerShell with `DATABASE_URL` set:

```powershell
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME"
.\scripts\check_globalgreeninvest_database.ps1
.\scripts\prepare_globalgreeninvest_primary_test.ps1
```

The prepare script runs migrations, the idempotent GlobalGreenInvest seed, and the diagnostic.

## 2. Render Backend

Create a Render Web Service:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Add Render env vars:

```env
APP_ENV=staging
APP_NAME=GlobalGreenInvest
DATABASE_URL=<Supabase session pooler URL>
JWT_SECRET=<strong random secret>
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
DEV_AUTH_ENABLED=true
TELEGRAM_SENDER_MODE=mock
TELEGRAM_REAL_SEND_SCOPE=pilot
TELEGRAM_BOT_TOKEN=
TELEGRAM_PILOT_CHAT_ID=
```

Deploy the backend.

Check:

```powershell
.\scripts\check_cloud_backend.ps1 -BackendBaseUrl "https://YOUR_BACKEND.onrender.com"
```

Render shell commands if needed:

```bash
cd backend
python -m alembic upgrade head
python scripts/seed_globalgreeninvest_demo.py
python scripts/check_globalgreeninvest_demo.py
```

## 3. Vercel Frontend

Create a Vercel project:

- Framework: Vite
- Root directory: `frontend`
- Install command: `pnpm install`
- Build command: `pnpm build`
- Output directory: `dist`

Add Vercel env vars:

```env
VITE_API_BASE_URL=https://YOUR_BACKEND.onrender.com/api/v1
VITE_PROJECT_SLUG=global-green-invest
VITE_DEV_TELEGRAM_MOCK=true
```

Do not add backend secrets to Vercel.

Deploy the frontend.

Important: if any `VITE_*` value is changed after the first deploy, redeploy the Vercel project. For this project, use:

```text
Vercel Project → Deployments → Redeploy → Use existing Build Cache: off
```

The cloud entrypoint for GlobalGreenInvest is:

```text
https://YOUR_FRONTEND.vercel.app/app
```

The root URL also redirects to `/app` when `VITE_PROJECT_SLUG=global-green-invest` is present at build time. If the root opens Wine Club, the deployed frontend bundle was built without the correct Vercel env or was not redeployed after env changes.

Login, loading, locked, banned, and community error states should show:

```text
🍀 ЗЕЛЁНЫЙ / TG Investor
project: global-green-invest
```

They should not show `CORE Wine Club` or `Дочь винодела` on `/app` or community `/admin/*` routes.

## 4. Update CORS

After Vercel gives you the frontend URL, update Render:

```env
CORS_ORIGINS=https://YOUR_FRONTEND.vercel.app,http://127.0.0.1:5173,http://localhost:5173
```

Redeploy backend after changing CORS.

## 5. Post-Deploy Checks

Open:

```text
https://YOUR_FRONTEND.vercel.app/app
https://YOUR_FRONTEND.vercel.app/app/products
https://YOUR_FRONTEND.vercel.app/admin/users
https://YOUR_FRONTEND.vercel.app/admin/requests
```

Test:

1. Create a product purchase request from a locked product.
2. Open `/admin/requests`.
3. Approve and grant access.
4. Refresh the product page.
5. Confirm locked materials unlock.

## 6. Telegram Pilot Later

Keep first deploy in mock mode:

```env
TELEGRAM_SENDER_MODE=mock
TELEGRAM_REAL_SEND_SCOPE=pilot
```

For the first real pilot:

```env
TELEGRAM_SENDER_MODE=real
TELEGRAM_REAL_SEND_SCOPE=pilot
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_PILOT_CHAT_ID=<your test chat id>
```

Then:

1. Restart backend.
2. Open `/admin/settings`.
3. Confirm pilot checklist is green.
4. Run dry-run first.
5. Process pending once.

Do not switch to `TELEGRAM_REAL_SEND_SCOPE=all` until production delivery rules are approved.

## 7. Readiness Commands

Before pushing/deploying:

```powershell
.\scripts\check_no_secrets.ps1
.\scripts\check_cloud_deploy_readiness.ps1
```

Backend smoke after Render deploy:

```powershell
.\scripts\check_cloud_backend.ps1 -BackendBaseUrl "https://YOUR_BACKEND.onrender.com"
```
