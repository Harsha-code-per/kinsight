import { expect, test } from "@playwright/test";

test("couple summary distinguishes an outage from an access denial", async ({ page }) => {
  let status = 503;
  await page.route("**/api/couples/*/assessment", (route) => route.fulfill({ status }));
  await page.goto("/couple");
  await expect(page.getByRole("alert").filter({ hasText: "The couple summary could not load" })).toBeVisible();
  await expect(page.getByText("The shared summary is currently unavailable.")).toHaveCount(0);

  status = 403;
  await page.reload();
  await expect(page.getByText("The shared summary is currently unavailable.")).toBeVisible();
  await expect(page.getByText("The couple summary could not load", { exact: false })).toHaveCount(0);
});

// Real-API content checks for the screens that used to look empty or garbled.
async function signInAs(page: import("@playwright/test").Page, role: RegExp) {
  await page.goto("/signin");
  await page.waitForLoadState("networkidle");
  await page.getByTestId("signin-submit").click();
  await expect(page).toHaveURL(/\/home$/);
  await page.getByRole("button", { name: role }).click();
}

test("audit tamper example leaves the shared audit chain intact", async ({ page }) => {
  await signInAs(page, /^Auditor/);
  await expect(page).toHaveURL(/\/governance$/);
  const chain = page.getByTestId("chain");
  await page.locator('[data-demo="verify"]').click();
  await expect(chain).toHaveAttribute("data-valid", "true");
  await page.locator('[data-demo="tamper"]').click();
  await expect(chain).toContainText("Chain broken: tampering detected");
  await page.locator('[data-demo="verify"]').click();
  await expect(chain).toHaveAttribute("data-valid", "true");
});

test("family circle shows three generations with readable labels", async ({ page }) => {
  await signInAs(page, /^Person A/);
  await page.goto("/family");
  const tree = page.getByRole("img", { name: "Pedigree" });
  await expect(tree).toBeVisible({ timeout: 60_000 });
  for (const label of ["GF", "GM", "P1", "S1", "P2", "S2", "A", "B"]) await expect(tree.getByText(label, { exact: true })).toBeVisible();
  await expect(tree.getByText("synthetic-a")).toHaveCount(0);
});

test("results use readable condition names, not raw ids", async ({ page }) => {
  await signInAs(page, /^Person A/);
  await expect(page).toHaveURL(/\/result/);
  await expect(page.getByText(/Inherited .* \(illustrative\)/).first()).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText("COND_001")).toHaveCount(0);
});

test("counsellor console has a real caseload", async ({ page }) => {
  await signInAs(page, /^Counsellor/);
  await expect(page).toHaveURL(/\/counsellor/);
  await expect(page.getByText("Nothing found.")).toHaveCount(0, { timeout: 60_000 });
  await expect(page.locator("tbody tr").first()).toBeVisible();
});

test("privacy centre lists the person's real access trail", async ({ page }) => {
  await signInAs(page, /^Person A/);
  await page.goto("/result");
  await page.goto("/privacy");
  await expect(page.getByText(/looked at your result/).first()).toBeVisible({ timeout: 60_000 });
});
