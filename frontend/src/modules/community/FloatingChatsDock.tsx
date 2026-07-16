import type { CommunityDashboardChatLink } from "./types";

export function FloatingChatsDock({ chats }: { chats: CommunityDashboardChatLink[] }) {
  if (chats.length === 0) {
    return null;
  }

  return (
    <aside className="community-floating-chats" aria-label="Актуальные чаты">
      <span className="community-floating-chats__label">Чаты</span>
      <div className="community-floating-chats__track">
        {chats.map((chat) => (
          <a
            key={chat.id}
            className="community-floating-chat-pill"
            href={chat.telegram_url}
            target="_blank"
            rel="noreferrer noopener"
            aria-label={`Открыть чат ${chat.title}`}
          >
            <span className="community-floating-chat-pill__dot" />
            <span>{chat.title}</span>
            <em>→</em>
          </a>
        ))}
      </div>
    </aside>
  );
}
