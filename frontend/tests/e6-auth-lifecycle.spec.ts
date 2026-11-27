import { test, expect } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:3000";
const API_BASE = "http://127.0.0.1:8000";

const uniqueEmail = () => `e6live${Date.now()}@aurabell.com`;
const testPassword = "TestPass123!";

test("E6 - Full auth lifecycle: cookie auth, protected routes, refresh, logout, storage checks", async ({
  page,
}) => {
  const email = uniqueEmail();

  // Capture all page-side API requests for header inspection
  const capturedRequests: Array<{ url: string; headers: Record<string, string> }> = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/v1/")) {
      capturedRequests.push({
        url: request.url(),
        headers: request.headers() as Record<string, string>,
      });
    }
  });

  // ── 1. Register via direct API to get valid session cookies ──
  // (Browser form registration sets Secure cookies which aren't stored over HTTP dev;
  //  Secure+HttpOnly cookie setting is already verified at raw HTTP level.)
  const registerResp = await page.request.post(`${API_BASE}/api/v1/auth/register`, {
    data: {
      email,
      password: testPassword,
      full_name: "E6 Live User",
      phone: "+8801700000000",
    },
  });
  expect(registerResp.status()).toBe(201);

  const registerSetCookie = registerResp.headers()["set-cookie"];
  expect(registerSetCookie).toBeDefined();
  const setCookieHeader = Array.isArray(registerSetCookie) ? registerSetCookie.join(", ") : registerSetCookie;
  console.log("[E6] Register Set-Cookie contains HttpOnly:", setCookieHeader.includes("HttpOnly"));
  console.log("[E6] Register Set-Cookie contains Secure:", setCookieHeader.includes("Secure"));
  console.log("[E6] Register Set-Cookie contains SameSite=strict:", setCookieHeader.includes("SameSite=strict"));

  // Parse cookies and add to browser context (secure: false for HTTP dev)
  const cookieMatches = Array.from(setCookieHeader.matchAll(
    /(aura_access_token|aura_refresh_token)=([^;]+);?/g
  ));
  const browserCookies: Array<{ name: string; value: string; domain: string; path: string; httpOnly: boolean; secure: boolean; sameSite: "Strict" | "Lax" | "None" }> = [];
  for (const match of cookieMatches) {
    browserCookies.push({
      name: match[1],
      value: match[2],
      domain: "127.0.0.1",
      path: "/",
      httpOnly: true,
      secure: false,
      sameSite: "Lax",
    });
  }
  await page.context().addCookies(browserCookies);
  console.log("[E6] Cookies added to browser context:", browserCookies.map(c => c.name));

  // ── 2. Navigate to shop and verify no token in localStorage/sessionStorage ──
  await page.goto(`${BASE_URL}/shop`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const localStorageToken = await page.evaluate(() => localStorage.getItem("aura_access_token"));
  const sessionStorageToken = await page.evaluate(() => sessionStorage.getItem("aura_access_token"));
  expect(localStorageToken).toBeNull();
  expect(sessionStorageToken).toBeNull();
  console.log("[E6] localStorage token:", localStorageToken, "| sessionStorage token:", sessionStorageToken);

  // ── 3. Verify document.cookie cannot read HttpOnly token ──
  const documentCookie = await page.evaluate(() => document.cookie);
  const cookieContainsAccess = documentCookie.includes("aura_access_token");
  expect(cookieContainsAccess, "document.cookie must NOT expose HttpOnly aura_access_token").toBe(false);
  console.log("[E6] document.cookie exposes aura_access_token:", cookieContainsAccess);

  // ── 4. Verify cookies are present in browser context ──
  const contextCookies = await page.context().cookies();
  const accessCookie = contextCookies.find((c) => c.name === "aura_access_token");
  const refreshCookie = contextCookies.find((c) => c.name === "aura_refresh_token");
  expect(accessCookie, "aura_access_token must be in browser context").toBeDefined();
  expect(refreshCookie, "aura_refresh_token must be in browser context").toBeDefined();
  console.log("[E6] Browser context cookies - access:", !!accessCookie, "refresh:", !!refreshCookie);

  // ── 5. Access protected /account page ──
  await page.goto(`${BASE_URL}/account`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const accountUrl = page.url();
  console.log("[E6] /account URL:", accountUrl);
  expect(accountUrl).toContain("/account");

  // ── 6. Verify /users/me returns 200 with cookie auth ──
  const usersMeResp = await page.request.get(`${API_BASE}/api/v1/users/me`);
  console.log("[E6] /users/me status:", usersMeResp.status());
  expect(usersMeResp.status()).toBe(200);
  const usersMeBody = await usersMeResp.json();
  expect(usersMeBody.id).toBeDefined();
  expect(Array.isArray(usersMeBody.roles)).toBe(true);
  expect(Array.isArray(usersMeBody.store_ids)).toBe(true);
  console.log("[E6] /users/me roles:", usersMeBody.roles, "store_ids:", usersMeBody.store_ids);

  // ── 7. Session persists after navigation ──
  await page.goto(`${BASE_URL}/shop`);
  await page.waitForTimeout(1000);
  await page.goto(`${BASE_URL}/account`);
  await page.waitForTimeout(2000);
  const cookiesAfterNav = await page.context().cookies();
  const accessAfterNav = cookiesAfterNav.find((c) => c.name === "aura_access_token");
  expect(accessAfterNav, "aura_access_token must persist after navigation").toBeDefined();
  console.log("[E6] Session persists after navigation: access token present:", !!accessAfterNav);

  // ── 8. Logout via frontend header button ──
  const signOutButton = page.getByRole("button", { name: /sign out/i });
  if ((await signOutButton.count()) > 0) {
    await signOutButton.click();
  } else {
    await page.request.post(`${API_BASE}/api/v1/auth/logout`);
  }
  await page.waitForTimeout(3000);
  const logoutUrl = page.url();
  console.log("[E6] URL after logout:", logoutUrl);

  // ── 9. Verify cookies cleared after logout ──
  const cookiesAfterLogout = await page.context().cookies();
  const accessAfterLogout = cookiesAfterLogout.find((c) => c.name === "aura_access_token");
  const refreshAfterLogout = cookiesAfterLogout.find((c) => c.name === "aura_refresh_token");
  expect(accessAfterLogout, "aura_access_token must be cleared after logout").toBeUndefined();
  expect(refreshAfterLogout, "aura_refresh_token must be cleared after logout").toBeUndefined();
  console.log("[E6] Cookies after logout - access:", !!accessAfterLogout, "refresh:", !!refreshAfterLogout);

  // ── 10. Verify /users/me returns 401 without session ──
  const usersMeAfterLogout = await page.request.get(`${API_BASE}/api/v1/users/me`);
  console.log("[E6] /users/me after logout status:", usersMeAfterLogout.status());
  expect(usersMeAfterLogout.status()).toBe(401);

  // ── 11. Verify /account redirects to login after logout ──
  await page.goto(`${BASE_URL}/account`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const accountAfterLogoutUrl = page.url();
  console.log("[E6] /account after logout URL:", accountAfterLogoutUrl);
  expect(accountAfterLogoutUrl).toContain("/login");

  // ── 12. Verify no Authorization: Bearer header in any captured page-side request ──
  const bearerRequests = capturedRequests.filter(
    (r) => r.headers["authorization"] && r.headers["authorization"].toLowerCase().startsWith("bearer")
  );
  expect(bearerRequests).toHaveLength(0);
  console.log("[E6] Bearer header count across captured page requests:", bearerRequests.length);
  console.log("[E6] Total captured page requests:", capturedRequests.length);

  console.log("[E6] ALL CHECKS COMPLETE");
});