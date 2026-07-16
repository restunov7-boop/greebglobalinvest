# Telegram Blogger Pilot Setup

This guide connects GlobalGreenInvest as a Telegram Mini App / Web App for a controlled blogger pilot.

## 1. Create The Bot

1. Open `@BotFather` in Telegram.
2. Create a bot with `/newbot`.
3. Save the token only in Render environment variables.
4. Set bot name, description, and photo.

Do not commit or paste the token into repo files.

## 2. Configure Telegram Web App Entry

Use BotFather to create/configure the Web App button or menu button.

Frontend URL:

```text
https://YOUR_FRONTEND.vercel.app/app
```

The app must be opened from Telegram so Telegram provides raw `initData`.

## 3. Render Backend Env

Set these in Render:

```env
APP_ENV=staging
DEV_AUTH_ENABLED=false
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_SENDER_MODE=real
TELEGRAM_REAL_SEND_SCOPE=pilot
TELEGRAM_PILOT_CHAT_ID=YOUR_TEST_CHAT_ID
```

Keep `TELEGRAM_REAL_SEND_SCOPE=pilot` for the first blogger test. Do not use `all`.

## 4. Vercel Frontend Env

Set these in Vercel:

```env
VITE_API_BASE_URL=https://YOUR_BACKEND.onrender.com/api/v1
VITE_PROJECT_SLUG=global-green-invest
VITE_DEV_TELEGRAM_MOCK=false
```

Vercel must not contain:

```text
DATABASE_URL
JWT_SECRET
TELEGRAM_BOT_TOKEN
```

After changing `VITE_*`, redeploy Vercel with build cache disabled.

## 5. First Blogger Access Flow

If the blogger has not opened the app before:

1. Blogger opens the bot/app once.
2. Backend validates Telegram `initData`.
3. User and TelegramIdentity are created.
4. GlobalGreenInvest ProjectUser is created with pending access.
5. Admin opens `/admin/users`.
6. Admin grants app access manually.
7. Blogger reopens the app.

If access is not active, the app shows `/app/locked`.

If moderation state is banned, the app shows `/app/banned`.

## 6. Pilot Notification Flow

1. Open `/admin/settings`.
2. Confirm:
   - sender mode: `real`
   - scope: `pilot`
   - token configured: yes
   - pilot target configured: yes
3. Create or publish an urgent insight.
4. Run dry-run first.
5. Process pending once.
6. Confirm only the pilot chat receives the message.

## 7. Local/Staging Debug Mode

For browser debugging without Telegram:

```env
VITE_DEV_TELEGRAM_MOCK=true
DEV_AUTH_ENABLED=true
TELEGRAM_SENDER_MODE=mock
```

This is not for production.
