import { execFile } from "node:child_process";
import { resolve } from "node:path";
import { promisify } from "node:util";
import { expect, test } from "@playwright/test";

test("the health record preview stays scoped and checks the latest FHIR version", async ({ page }) => {
  const fhirUrl = process.env.KINSIGHT_FHIR_SANDBOX_URL;
  test.skip(!fhirUrl || process.env.NEXT_PUBLIC_FHIR_SANDBOX !== "1", "Requires a disposable seeded HAPI server");
  test.setTimeout(90_000);
  const upload = (args: string[]) => promisify(execFile)(process.env.PYTHON ?? "python", [
    "-m", "scripts.export_fhir_bundles", "--upload", fhirUrl!, ...args,
  ], { cwd: resolve(".."), timeout: 30_000 });
  await upload([]);
  await page.goto("/signin");
  await page.getByTestId("signin-submit").click();
  await expect(page).toHaveURL(/\/home$/);
  await page.getByRole("button", { name: /^Person A/ }).click();
  await expect(page).toHaveURL(/\/result$/);
  const panel = page.getByRole("region", { name: "Health record preview" });
  const load = panel.getByRole("button", { name: "Load latest report" });
  await load.click();
  await expect(panel.getByRole("status")).toContainText("need counsellor review");
  await expect(panel.getByRole("listitem")).toHaveCount(28);
  await expect(panel.locator("time")).toHaveAttribute("dateTime", /^2026-01-01/);

  await upload(["--correction"]);
  await load.click();
  await expect(panel.getByRole("status")).toContainText("need counsellor review");
  await expect(panel.getByRole("listitem")).toHaveCount(27);
  await expect(panel.locator("time")).toHaveAttribute("dateTime", /^2026-01-02/);
});
