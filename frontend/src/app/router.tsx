import { createBrowserRouter, Navigate } from "react-router-dom";

import { AdminGuard } from "./guards/AdminGuard";
import { AuthGuard } from "./guards/AuthGuard";
import { AdminLayout } from "./layout/AdminLayout";
import { AppShell } from "./layouts/AppShell";
import { BottlePage } from "../modules/bottle/BottlePage";
import {
  CommunityAdminChatsPage,
  CommunityAdminExchangesPage,
  CommunityAdminGuard,
  CommunityAdminInsightsPage,
  CommunityAdminLayout,
  CommunityAdminPostsPage,
  CommunityAdminProductsPage,
  CommunityAdminPurchaseRequestsPage,
  CommunityAdminSettingsPage,
  CommunityAdminUsersPage,
  CommunityBannedPage,
  CommunityDashboardPage,
  CommunityExchangesPage,
  CommunityInsightPage,
  CommunityLayout,
  CommunityLockedPage,
  CommunityPostPage,
  CommunityProductDetailPage,
  CommunityProductsPage,
  CommunityProfilePage,
  CommunityRulesPage,
  CommunitySettingsPage,
} from "../modules/community";
import { DiaryNoteDetailPage } from "../modules/diary/DiaryNoteDetailPage";
import { DiaryNoteFormPage } from "../modules/diary/DiaryNoteFormPage";
import { DiaryPage } from "../modules/diary/DiaryPage";
import { DiscoveriesPage } from "../modules/discoveries/DiscoveriesPage";
import { DiscoveryDetailPage } from "../modules/discoveries/DiscoveryDetailPage";
import { HomePage } from "../modules/home/HomePage";
import { LearningPathDetailPage } from "../modules/learning/LearningPathDetailPage";
import { LearningPathsPage } from "../modules/learning/LearningPathsPage";
import { LessonDetailPage } from "../modules/learning/LessonDetailPage";
import { MyPathPage } from "../modules/my-path/MyPathPage";
import { OnboardingPage } from "../modules/onboarding/OnboardingPage";
import { ProgressActivityPage } from "../modules/progress/ProgressActivityPage";
import { TasteProfilePage } from "../modules/taste-profile/TasteProfilePage";
import { PlaceholderPage } from "../shared/ui/PlaceholderPage";

const projectSlug = import.meta.env.VITE_PROJECT_SLUG?.trim();
const isGlobalGreenInvest = projectSlug === "global-green-invest";
const defaultEntryPath = isGlobalGreenInvest ? "/app" : "/home";

if (import.meta.env.DEV || import.meta.env.MODE === "staging") {
  console.info("[CORE] frontend project env", {
    projectSlug: projectSlug || "<unset>",
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "<default>",
    defaultEntryPath,
  });
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to={defaultEntryPath} replace />,
  },
  {
    path: "/loading",
    element: <PlaceholderPage title="Loading" />,
  },
  {
    path: "/onboarding",
    element: (
      <AuthGuard>
        <OnboardingPage />
      </AuthGuard>
    ),
  },
  {
    path: "/app",
    element: (
      <AuthGuard>
        <CommunityLayout />
      </AuthGuard>
    ),
    children: [
      { index: true, element: <CommunityDashboardPage /> },
      { path: "profile", element: <CommunityProfilePage /> },
      { path: "exchanges", element: <CommunityExchangesPage /> },
      { path: "products", element: <CommunityProductsPage /> },
      { path: "products/:productId", element: <CommunityProductDetailPage /> },
      { path: "settings", element: <CommunitySettingsPage /> },
      { path: "posts/:postId", element: <CommunityPostPage /> },
      { path: "insights/:insightId", element: <CommunityInsightPage /> },
      { path: "locked", element: <CommunityLockedPage /> },
      { path: "banned", element: <CommunityBannedPage /> },
      { path: "rules", element: <CommunityRulesPage /> },
    ],
  },
  {
    element: (
      <AuthGuard>
        <AppShell />
      </AuthGuard>
    ),
    children: [
      { path: "/home", element: <HomePage /> },
      { path: "/bottle", element: <BottlePage /> },
      { path: "/progress", element: <ProgressActivityPage /> },
      { path: "/my-path", element: <MyPathPage /> },
      { path: "/discoveries", element: <DiscoveriesPage /> },
      { path: "/discoveries/:slug", element: <DiscoveryDetailPage /> },
      { path: "/learn", element: <LearningPathsPage /> },
      { path: "/learn/lessons/:lessonSlug", element: <LessonDetailPage /> },
      { path: "/learn/:pathSlug", element: <LearningPathDetailPage /> },
      { path: "/diary", element: <DiaryPage /> },
      { path: "/diary/new", element: <DiaryNoteFormPage /> },
      { path: "/diary/:noteId", element: <DiaryNoteDetailPage /> },
      { path: "/diary/:noteId/edit", element: <DiaryNoteFormPage /> },
      { path: "/taste-profile", element: <TasteProfilePage /> },
      { path: "/club", element: <PlaceholderPage title="Клуб" /> },
      { path: "/premium", element: <PlaceholderPage title="Premium" /> },
      { path: "/notifications", element: <PlaceholderPage title="Notifications" /> },
      { path: "/settings", element: <PlaceholderPage title="Settings" /> },
    ],
  },
  {
    path: "/admin",
    element: (
      <AuthGuard>
        <AdminGuard>
          <AdminLayout />
        </AdminGuard>
      </AuthGuard>
    ),
    children: [
      { index: true, element: <PlaceholderPage title="Admin" /> },
      { path: "dashboard", element: <PlaceholderPage title="Admin Dashboard" /> },
    ],
  },
  {
    path: "/admin",
    element: (
      <AuthGuard>
        <CommunityAdminGuard>
          <CommunityAdminLayout />
        </CommunityAdminGuard>
      </AuthGuard>
    ),
    children: [
      { path: "posts", element: <CommunityAdminPostsPage /> },
      { path: "insights", element: <CommunityAdminInsightsPage /> },
      { path: "chats", element: <CommunityAdminChatsPage /> },
      { path: "exchanges", element: <CommunityAdminExchangesPage /> },
      { path: "products", element: <CommunityAdminProductsPage /> },
      { path: "requests", element: <CommunityAdminPurchaseRequestsPage /> },
      { path: "users", element: <CommunityAdminUsersPage /> },
      { path: "settings", element: <CommunityAdminSettingsPage /> },
    ],
  },
  {
    path: "*",
    element: <Navigate to={defaultEntryPath} replace />,
  },
]);
