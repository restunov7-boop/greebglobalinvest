import type { CommunityPlaceholderPage } from "./types";

type CommunityPlaceholderProps = CommunityPlaceholderPage & {
  eyebrow?: string;
};

export function CommunityPlaceholder({ title, description, eyebrow = "GlobalGreenInvest" }: CommunityPlaceholderProps) {
  return (
    <section className="community-placeholder">
      <div className="community-placeholder__eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p>{description}</p>
    </section>
  );
}

