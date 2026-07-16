import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import {
  getCommunityAdminNotificationSenderStatus,
  listCommunityAdminNotifications,
  processCommunityAdminPendingNotifications,
} from "../api";
import type {
  CommunityAdminNotificationItem,
  CommunityAdminNotificationProcessSummary,
  CommunityAdminNotificationSenderStatus,
} from "../types";

function formatDate(value: string | null): string {
  if (!value) {
    return "Дата не задана";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function notificationStatusLabel(status: CommunityAdminNotificationItem["status"]): string {
  const labels: Record<CommunityAdminNotificationItem["status"], string> = {
    pending: "Ожидает",
    mock_sent: "Mock-обработано",
    sent: "Отправлено",
    skipped: "Пропущено",
    failed: "Ошибка",
  };
  return labels[status] ?? status;
}

function notificationReasonLabel(reason: string): string {
  const labels: Record<string, string> = {
    real_mode_pilot_recipient_mismatch: "Не pilot-получатель",
    real_mode_pilot_target_missing: "Pilot-получатель не настроен",
    missing_telegram_identity: "Нет Telegram identity",
    notifications_disabled: "Уведомления выключены",
    recipient_not_eligible: "Нет активного доступа",
    recipient_not_found: "Получатель не найден",
    insight_not_found: "Инсайд не найден",
    telegram_bot_token_missing: "Токен бота не настроен",
    missing_bot_token: "Токен бота не настроен",
    no_telegram_identity: "Нет Telegram identity",
    telegram_network_error: "Сетевая ошибка Telegram",
  };
  if (reason.startsWith("telegram_api_error")) {
    return "Ошибка Telegram API";
  }
  return labels[reason] ?? reason;
}

function senderWarningText(senderStatus: CommunityAdminNotificationSenderStatus | null): string {
  if (!senderStatus || senderStatus.mode === "mock") {
    return "Demo-режим: реальные Telegram-сообщения не отправляются.";
  }
  if (senderStatus.real_send_scope === "pilot" && senderStatus.pilot_target_configured) {
    return "Real pilot: реальные сообщения могут уйти только одному тестовому получателю.";
  }
  if (senderStatus.real_send_scope === "pilot") {
    return "Real pilot включён, но тестовый получатель не настроен. Реальная отправка будет заблокирована.";
  }
  return "Внимание: real all. Обработка pending отправит реальные сообщения всем подходящим участникам.";
}

type ReadinessItem = {
  title: string;
  description: string;
  state: "pass" | "warning" | "error";
};

function readinessStateLabel(state: ReadinessItem["state"]): string {
  const labels: Record<ReadinessItem["state"], string> = {
    pass: "OK",
    warning: "Внимание",
    error: "Блокер",
  };
  return labels[state];
}

function buildReadinessChecklist(
  senderStatus: CommunityAdminNotificationSenderStatus | null,
  pendingCount: number,
  hasDryRun: boolean,
): ReadinessItem[] {
  const mode = senderStatus?.mode ?? "mock";
  const scope = senderStatus?.real_send_scope ?? "pilot";
  const tokenConfigured = senderStatus?.token_configured ?? false;
  const pilotConfigured = senderStatus?.pilot_target_configured ?? false;

  return [
    {
      title: "Режим отправки",
      description:
        mode === "real"
          ? "Real - включена реальная отправка."
          : "Demo/mock - реальные сообщения не отправляются.",
      state: mode === "real" ? "warning" : "pass",
    },
    {
      title: "Токен бота",
      description:
        mode === "mock"
          ? "В mock-режиме токен не нужен."
          : tokenConfigured
            ? "Токен настроен."
            : "Токен не настроен - реальные сообщения не уйдут.",
      state: mode === "real" && !tokenConfigured ? "error" : "pass",
    },
    {
      title: "Область real-отправки",
      description:
        scope === "all"
          ? "All - может отправить всем подходящим участникам."
          : "Pilot - отправка ограничена тестовым получателем.",
      state: mode === "real" && scope === "all" ? "error" : "pass",
    },
    {
      title: "Pilot-получатель",
      description:
        scope === "all"
          ? "В all-режиме pilot-ограничение не используется."
          : pilotConfigured
            ? "Pilot-получатель настроен."
            : mode === "real"
              ? "Pilot-получатель не настроен - отправка будет заблокирована."
              : "Pilot-получатель не нужен для mock-режима.",
      state: mode === "real" && scope === "pilot" && !pilotConfigured ? "error" : "pass",
    },
    {
      title: "Pending-уведомления",
      description: pendingCount > 0 ? `В очереди: ${pendingCount}.` : "Pending-уведомлений нет.",
      state: pendingCount > 0 ? "warning" : "pass",
    },
    {
      title: "Dry-run",
      description: hasDryRun
        ? "Dry-run выполнен. Проверьте результат перед обработкой."
        : mode === "real"
          ? "Сначала выполните dry-run."
          : "Dry-run доступен для проверки очереди.",
      state: mode === "real" && !hasDryRun ? "warning" : "pass",
    },
  ];
}

export function CommunityAdminSettingsPage() {
  const [items, setItems] = useState<CommunityAdminNotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pendingTotal, setPendingTotal] = useState(0);
  const [summary, setSummary] = useState<CommunityAdminNotificationProcessSummary | null>(null);
  const [senderStatus, setSenderStatus] = useState<CommunityAdminNotificationSenderStatus | null>(null);
  const [hasDryRun, setHasDryRun] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [payload, pendingPayload, statusPayload] = await Promise.all([
        listCommunityAdminNotifications({ type: "urgent_insight", limit: 50 }),
        listCommunityAdminNotifications({ type: "urgent_insight", status: "pending", limit: 1 }),
        getCommunityAdminNotificationSenderStatus(),
      ]);
      setItems(payload.items);
      setTotal(payload.total);
      setPendingTotal(pendingPayload.total);
      setSenderStatus(statusPayload);
      setAccessDenied(false);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить очередь уведомлений.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  const readinessChecklist = useMemo(
    () => buildReadinessChecklist(senderStatus, pendingTotal, hasDryRun),
    [senderStatus, pendingTotal, hasDryRun],
  );
  const isRealMode = senderStatus?.mode === "real";
  const processDisabled = isProcessing || (isRealMode && !hasDryRun);

  const handleProcess = async (dryRun: boolean) => {
    if (!dryRun && senderStatus?.mode === "real") {
      if (!hasDryRun) {
        window.alert("Сначала выполните dry-run и проверьте результат.");
        return;
      }
      if (senderStatus.real_send_scope === "all") {
        const confirmation = window.prompt(
          "Это может отправить реальные Telegram-сообщения всем активным участникам. Введите REAL для подтверждения.",
        );
        if (confirmation !== "REAL") {
          return;
        }
      } else {
        const confirmed = window.confirm("Отправить тестовое Telegram-сообщение только pilot-получателю?");
        if (!confirmed) {
          return;
        }
      }
    }
    setIsProcessing(true);
    setError(null);
    try {
      const result = await processCommunityAdminPendingNotifications({ limit: 50, dry_run: dryRun });
      setSummary(result);
      if (dryRun) {
        setHasDryRun(true);
      } else if (senderStatus?.mode === "real") {
        setHasDryRun(false);
      }
      await loadNotifications();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Не удалось обработать очередь уведомлений.");
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return <LoadingState title="Загружаем настройки" description="Проверяем очередь срочных Telegram-уведомлений." />;
  }

  if (accessDenied) {
    return <EmptyState title="Нет доступа" description="Backend не подтвердил права администратора GlobalGreenInvest." />;
  }

  if (error) {
    return <ErrorState title="Настройки недоступны" description={error} />;
  }

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>GlobalGreenInvest admin</span>
          <h1>Telegram-уведомления</h1>
          <p>{total} записей в очереди срочных инсайдов</p>
        </div>
      </header>

      <div className="community-admin-card">
        <div className="community-admin-card__meta">
          <span>Pilot-проверка Telegram</span>
          <span>{pendingTotal} pending</span>
        </div>
        <h2>Pilot-проверка Telegram</h2>
        <div className="community-admin-card__stats">
          {readinessChecklist.map((item) => (
            <span key={item.title}>
              {readinessStateLabel(item.state)} · {item.title}: {item.description}
            </span>
          ))}
        </div>
      </div>

      <div className="community-admin-card">
        <div className="community-admin-card__meta">
          <span>Режим отправки: {senderStatus?.mode === "real" ? "real" : "demo/mock"}</span>
          <span>Scope: {senderStatus?.real_send_scope ?? "pilot"}</span>
          <span>Pilot target: {senderStatus?.pilot_target_configured ? "yes" : "no"}</span>
          <span>{pendingTotal} pending</span>
        </div>
        <h2>{senderStatus?.mode === "real" ? "Real-отправка Telegram" : "Безопасная demo-обработка"}</h2>
        <p>{senderWarningText(senderStatus)}</p>
        <div className="community-admin-card__actions">
          <button type="button" onClick={() => void handleProcess(true)} disabled={isProcessing}>
            Проверить без обработки
          </button>
          <button
            className="community-admin-button community-admin-button--primary"
            type="button"
            onClick={() => void handleProcess(false)}
            disabled={processDisabled}
          >
            Обработать pending
          </button>
        </div>
        {isRealMode && !hasDryRun && <p>Для real-режима сначала выполните dry-run в этой сессии страницы.</p>}
      </div>

      {summary && (
        <div className="community-admin-card">
          <div className="community-admin-card__meta">
            <span>{summary.dry_run ? "Dry-run" : summary.mode === "real" ? "Real-обработка" : "Demo-обработка"}</span>
            <span>Осталось pending: {summary.remaining_pending}</span>
          </div>
          <h2>{summary.dry_run ? "Результат dry-run" : "Результат обработки"}</h2>
          {summary.dry_run && <p>Dry-run не отправлял сообщения.</p>}
          <div className="community-admin-card__stats">
            <span>Обработано: {summary.processed}</span>
            <span>{summary.dry_run ? "Будет обработано/mock" : "Mock-обработано"}: {summary.sent_mock}</span>
            <span>{summary.dry_run ? "Будет отправлено real" : "Real-отправлено"}: {summary.sent}</span>
            <span>{summary.dry_run ? "Будет пропущено" : "Пропущено"}: {summary.skipped}</span>
            <span>{summary.dry_run ? "Ошибки/блокировки" : "Ошибки"}: {summary.failed}</span>
          </div>
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState title="Очередь пуста" description="Опубликуйте срочный инсайд, чтобы создать pending-записи." />
      ) : (
        <div className="community-admin-list">
          {items.map((item) => (
            <article className="community-admin-card" key={item.id}>
              <div className="community-admin-card__meta">
                <span>{notificationStatusLabel(item.status)}</span>
                <span>{formatDate(item.created_at)}</span>
              </div>
              <h2>{item.insight_title ?? item.title}</h2>
              <p>{item.body}</p>
              <div className="community-admin-card__stats">
                <span>@{item.telegram_username ?? "no_telegram"}</span>
                <span>{item.sent_at ? `Обработано: ${formatDate(item.sent_at)}` : "Не обработано"}</span>
                {item.mock_message_id && <span>{item.mock_message_id}</span>}
                {item.error_message && <span>{notificationReasonLabel(item.error_message)}</span>}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
