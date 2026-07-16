import { useEffect, useState } from "react";
import type { PropsWithChildren } from "react";

import { ApiError } from "../../../shared/api/client";

import { getCommunityAdminInfo } from "../api";

import { CommunityAdminNoAccessPage } from "./CommunityAdminNoAccessPage";

type GuardState = "loading" | "allowed" | "denied" | "error";

export function CommunityAdminGuard({ children }: PropsWithChildren) {
  const [state, setState] = useState<GuardState>("loading");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function checkAccess() {
      setState("loading");
      setMessage(null);
      try {
        await getCommunityAdminInfo();
        if (isMounted) setState("allowed");
      } catch (error) {
        if (!isMounted) return;
        if (error instanceof ApiError && error.status === 403) {
          setState("denied");
          return;
        }
        setMessage(error instanceof Error ? error.message : "Не удалось проверить доступ к админ-панели.");
        setState("error");
      }
    }

    void checkAccess();

    return () => {
      isMounted = false;
    };
  }, []);

  if (state === "loading") {
    return (
      <section className="community-admin-state" role="status" aria-live="polite">
        <span>Проверка доступа</span>
        <h1>Открываем админ-панель</h1>
        <p>Проверяем права администратора проекта GlobalGreenInvest.</p>
      </section>
    );
  }

  if (state === "denied") return <CommunityAdminNoAccessPage />;

  if (state === "error") {
    return (
      <section className="community-admin-state community-admin-state--error" role="alert">
        <span>Ошибка доступа</span>
        <h1>Не удалось открыть админ-панель</h1>
        <p>{message ?? "Проверьте, что backend запущен, и попробуйте снова."}</p>
        <button
          className="community-admin-button community-admin-button--primary"
          type="button"
          onClick={() => window.location.reload()}
        >
          Повторить
        </button>
      </section>
    );
  }

  return <>{children}</>;
}
