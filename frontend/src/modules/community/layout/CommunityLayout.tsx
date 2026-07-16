import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

import { CommunityHeader } from "./CommunityHeader";
import { CommunitySidebar } from "./CommunitySidebar";

export function CommunityLayout() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    if (!isMenuOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isMenuOpen]);

  return (
    <div className="community-shell">
      <CommunitySidebar isOpen={isMenuOpen} onClose={() => setIsMenuOpen(false)} />
      {isMenuOpen && (
        <button
          className="community-drawer-overlay"
          type="button"
          aria-label="Закрыть меню"
          onClick={() => setIsMenuOpen(false)}
        />
      )}
      <div className="community-shell__body">
        <CommunityHeader onMenuOpen={() => setIsMenuOpen(true)} />
        <main className="community-shell__main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
