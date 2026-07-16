# Vercel Frontend Setup

## Project Settings

- Framework preset: Vite
- Root directory: `frontend`
- Install command:

```bash
pnpm install
```

- Build command:

```bash
pnpm build
```

- Output directory:

```text
dist
```

`frontend/vercel.json` rewrites all routes to `/`, so direct links like `/app/products` and `/admin/requests` work as SPA routes.

## Required Environment Variables

Only use `VITE_*` variables in Vercel. Backend secrets must not be added to Vercel.

```env
VITE_API_BASE_URL=https://YOUR_BACKEND.onrender.com/api/v1
VITE_PROJECT_SLUG=global-green-invest
VITE_DEV_TELEGRAM_MOCK=true
```

For a real Telegram WebApp production setup, `VITE_DEV_TELEGRAM_MOCK` must be disabled after login is ready.

Never add these to Vercel:

```text
DATABASE_URL
JWT_SECRET
TELEGRAM_BOT_TOKEN
```

## Smoke Pages

After deploy, open:

```text
https://YOUR_FRONTEND.vercel.app/app
https://YOUR_FRONTEND.vercel.app/app/products
https://YOUR_FRONTEND.vercel.app/admin/users
https://YOUR_FRONTEND.vercel.app/admin/requests
```
