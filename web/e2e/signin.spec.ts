import { expect, test } from "@playwright/test";
import languages from "../messages/languages.json";

test("landing opens the fictional demo without collecting credentials", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("ks_user", "old-demo-username"));
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Ask Kin" })).toHaveCount(0);
  await expect(page.getByTestId("fictional-banner")).toHaveCount(0);
  await page.getByTestId("hero-signin").click();
  await expect(page).toHaveURL(/\/signin$/);

  await expect(page.locator("input[name=username], input[type=password]")).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => localStorage.getItem("ks_user"))).toBeNull();

  await page.getByTestId("signin-submit").click();
  await expect(page).toHaveURL(/\/home$/);
  await expect(page.getByTestId("fictional-banner")).toBeVisible();
  await expect(page.getByRole("button", { name: "Ask Kin" })).toBeVisible();
});

test("demo entry works with reduced motion and in Arabic", async ({ page }) => {
  // Set before any page script runs: the language provider writes the stored language back after it loads.
  await page.addInitScript(() => localStorage.setItem("ks_lang", "ar"));
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/signin");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.locator("video")).toHaveCount(0);
  await page.getByTestId("signin-submit").click();
  await expect(page).toHaveURL(/\/home$/);
});

test("a retired language preference returns to the shipped language menu", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("ks_lang", "ur"));
  await page.goto("/home");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("ks_lang"))).toBe("en");
  const languagesMenu = page.getByTestId("language-select").first();
  await expect(languagesMenu).toHaveValue("en");
  await expect(languagesMenu.getByRole("option")).toHaveCount(languages.length);
});
