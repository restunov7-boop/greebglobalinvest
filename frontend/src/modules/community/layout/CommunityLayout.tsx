import { Outlet } from "react-router-dom";

import { CommunityHeader } from "./CommunityHeader";
import { CommunitySidebar } from "./CommunitySidebar";

export function CommunityLayout() {
  return (
    <div className="community-shell">
      <CommunitySidebar />
      <div className="community-shell__body">
        <CommunityHeader />
        <main className="community-shell__main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

