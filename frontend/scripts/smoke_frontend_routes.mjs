const baseUrl = process.env.FRONTEND_BASE_URL || "http://127.0.0.1:5173";

const routes = [
  "/home",
  "/app",
  "/app/profile",
  "/app/exchanges",
  "/app/products",
  "/app/products/demo-product",
  "/app/settings",
  "/app/posts/demo-post",
  "/app/insights/demo-insight",
  "/app/locked",
  "/app/banned",
  "/app/rules",
  "/my-path",
  "/bottle",
  "/progress",
  "/discoveries",
  "/learn",
  "/diary",
  "/taste-profile",
  "/admin",
  "/admin/posts",
  "/admin/insights",
  "/admin/chats",
  "/admin/exchanges",
  "/admin/products",
  "/admin/requests",
  "/admin/users",
  "/admin/settings",
  "/onboarding",
  "/unknown-route-for-smoke",
];

async function checkRoute(route) {
  const url = `${baseUrl}${route}`;

  const response = await fetch(url, {
    redirect: "follow",
    headers: {
      Accept: "text/html",
    },
  });

  if (!response.ok) {
    throw new Error(`${route} returned HTTP ${response.status}`);
  }

  const contentType = response.headers.get("content-type") || "";
  const body = await response.text();

  const looksLikeHtml =
    contentType.includes("text/html") ||
    body.toLowerCase().includes("<!doctype html") ||
    body.toLowerCase().includes("<html");

  if (!looksLikeHtml) {
    throw new Error(`${route} did not return HTML`);
  }

  if (!body.includes('id="root"')) {
    throw new Error(`${route} did not return React root HTML`);
  }

  console.log(`[OK] route ${route}`);
}

async function main() {
  console.log(`[INFO] Checking frontend routes at ${baseUrl}`);

  for (const route of routes) {
    await checkRoute(route);
  }

  console.log("[OK] frontend route smoke complete");
}

main().catch((error) => {
  console.error("[ERROR] frontend route smoke failed");
  console.error(error.message);
  process.exit(1);
});
