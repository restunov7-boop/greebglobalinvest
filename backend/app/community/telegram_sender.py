from dataclasses import dataclass
from uuid import UUID

import httpx

from app.config import Settings
from app.community.models import CommunityInsight
from app.users.models import TelegramIdentity


@dataclass(frozen=True)
class TelegramSendResult:
    status: str
    message_id: str | None = None
    error_message: str | None = None


class MockTelegramSender:
    mode = "mock"
    ready = True
    dry_run_status = "mock_sent"

    def send_message(self, telegram: TelegramIdentity | None, message: str) -> TelegramSendResult:
        if telegram is None or not telegram.telegram_id:
            return TelegramSendResult(status="skipped", error_message="missing_telegram_identity")
        if not message.strip():
            return TelegramSendResult(status="failed", error_message="empty_message")
        return TelegramSendResult(status="mock_sent", message_id=f"mock-{telegram.telegram_id}")


class MisconfiguredTelegramSender:
    mode = "real"
    ready = False
    dry_run_status = "failed"

    def __init__(self, error_message: str) -> None:
        self.error_message = error_message

    def send_message(self, telegram: TelegramIdentity | None, message: str) -> TelegramSendResult:
        return TelegramSendResult(status="failed", error_message=self.error_message)


class RealTelegramSender:
    mode = "real"
    ready = True
    dry_run_status = "sent"

    def __init__(
        self,
        bot_token: str,
        api_base_url: str = "https://api.telegram.org",
        timeout_seconds: float = 10,
    ) -> None:
        self._bot_token = bot_token
        self._api_base_url = api_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def send_message(self, telegram: TelegramIdentity | None, message: str) -> TelegramSendResult:
        if telegram is None or not telegram.telegram_id:
            return TelegramSendResult(status="skipped", error_message="missing_telegram_identity")
        if not message.strip():
            return TelegramSendResult(status="failed", error_message="empty_message")

        url = f"{self._api_base_url}/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": telegram.telegram_id,
            "text": message,
            "disable_web_page_preview": True,
        }
        try:
            response = httpx.post(url, json=payload, timeout=self._timeout_seconds)
        except httpx.TimeoutException:
            return TelegramSendResult(status="failed", error_message="telegram_timeout")
        except httpx.HTTPError:
            return TelegramSendResult(status="failed", error_message="telegram_network_error")

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code != 200:
            description = data.get("description") if isinstance(data, dict) else None
            return TelegramSendResult(
                status="failed",
                error_message=_safe_telegram_error(description, response.status_code),
            )

        if isinstance(data, dict) and data.get("ok") is False:
            return TelegramSendResult(status="failed", error_message=_safe_telegram_error(data.get("description"), response.status_code))

        message_id: str | None = None
        if isinstance(data, dict):
            result = data.get("result")
            if isinstance(result, dict) and result.get("message_id") is not None:
                message_id = str(result["message_id"])
        return TelegramSendResult(status="sent", message_id=message_id)


def _safe_telegram_error(description: object, status_code: int) -> str:
    if isinstance(description, str) and description.strip():
        return f"telegram_api_error_{status_code}: {description.strip()[:180]}"
    return f"telegram_api_error_{status_code}"


def normalized_telegram_sender_mode(settings: Settings) -> str:
    mode = settings.telegram_sender_mode.strip().lower()
    if mode not in ("mock", "real"):
        return "mock"
    return mode


def normalized_telegram_real_send_scope(settings: Settings) -> str:
    scope = settings.telegram_real_send_scope.strip().lower()
    if scope not in ("pilot", "all"):
        return "pilot"
    return scope


def get_telegram_sender(settings: Settings) -> MockTelegramSender | RealTelegramSender | MisconfiguredTelegramSender:
    mode = normalized_telegram_sender_mode(settings)
    if mode == "mock":
        return MockTelegramSender()

    token = settings.telegram_bot_token.strip()
    if not token or token == "change_me":
        return MisconfiguredTelegramSender("telegram_bot_token_missing")
    return RealTelegramSender(
        bot_token=token,
        api_base_url=settings.telegram_api_base_url,
        timeout_seconds=settings.telegram_send_timeout_seconds,
    )


def compose_urgent_insight_message(insight: CommunityInsight) -> str:
    title = insight.title.strip()
    excerpt = insight.excerpt.strip()
    return (
        f"Срочный инсайд: {title}\n\n"
        f"{excerpt}\n\n"
        "Откройте приложение, чтобы прочитать полностью."
    )


def mock_message_id(notification_id: UUID, telegram: TelegramIdentity) -> str:
    return f"mock-{telegram.telegram_id}-{str(notification_id)[:8]}"
