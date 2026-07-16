export const GGI_BRAND_NAME = "🍀 ЗЕЛЁНЫЙ / TG Investor";

export function accessStateLabel(value: string): string {
  return (
    {
      pending: "Ожидает",
      active: "Активен",
      expired: "Истёк",
      revoked: "Отозван",
    }[value] ?? value
  );
}

export function moderationStateLabel(value: string): string {
  return (
    {
      normal: "Норма",
      banned: "Забанен",
    }[value] ?? value
  );
}

export function roleLabel(value: string): string {
  return (
    {
      owner: "Владелец",
      admin: "Админ",
      member: "Участник",
      moderator: "Модератор",
    }[value] ?? value
  );
}

export function contentStatusLabel(value: string): string {
  return (
    {
      draft: "Черновик",
      scheduled: "Запланировано",
      published: "Опубликовано",
      hidden: "Скрыто",
    }[value] ?? value
  );
}

export function productAccessSourceLabel(value: string): string {
  return (
    {
      manual: "Ручной доступ",
      legacy_import: "Импорт",
      csv_import: "CSV",
      sql_import: "SQL",
      future_payment: "Оплата",
    }[value] ?? value
  );
}

export function materialTypeLabel(value: string): string {
  return (
    {
      text: "Текст",
      link: "Ссылка",
      file_view: "Файл",
      external_site: "Внешний сайт",
    }[value] ?? value
  );
}
