import { expect, test } from "@playwright/test";

test("a lab correction invalidates the open participant view until reviewed", async ({ page, browser }) => {
  test.skip(process.env.NEXT_PUBLIC_LAB_SANDBOX !== "1", "This suite needs the opt-in lab sandbox");
  test.setTimeout(60_000);
  const waitForPoll = expect.configure({ timeout: 12_000 });
  const workstation = await browser.newPage();
  try {
    await page.goto("/lab-sandbox");
    await workstation.goto("/lab-sandbox");
    await page.getByRole("button", { name: "Share for review" }).click();
    await expect(page.getByText("Shared for review", { exact: true })).toBeVisible();
    await workstation.getByRole("button", { name: "Demo operator", exact: true }).click();
    await workstation.getByRole("button", { name: "Send final report" }).click();
    await expect(workstation.getByText("Lab report received")).toBeVisible();
    await waitForPoll(page.getByText("Awaiting counsellor review · Revision 1")).toBeVisible();
    await expect(page.getByText("Carrier finding", { exact: true })).toHaveCount(0);

    await workstation.getByRole("button", { name: "Counsellor", exact: true }).click();
    await workstation.getByRole("button", { name: "Approve this revision" }).click();
    await waitForPoll(page.getByText("Carrier finding", { exact: true })).toBeVisible();

    await workstation.getByRole("button", { name: "Demo operator", exact: true }).click();
    await workstation.getByRole("spinbutton", { name: "Revision" }).fill("2");
    await workstation.getByRole("button", { name: "Send correction" }).click();
    await expect(workstation.getByText("Lab report received")).toBeVisible();
    await waitForPoll(page.getByText("Awaiting counsellor review · Revision 2")).toBeVisible();
    await expect(page.getByText("Carrier finding", { exact: true })).toHaveCount(0);
    await expect(page.getByText("Uncertain finding", { exact: true })).toHaveCount(0);

    await workstation.getByRole("button", { name: "Counsellor", exact: true }).click();
    await expect(workstation.getByText("Uncertain finding", { exact: true })).toBeVisible();
    await workstation.getByRole("button", { name: "Approve this revision" }).click();
    await waitForPoll(page.getByText("Uncertain finding", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Person B", exact: true }).click();
    await expect(page.getByText("No lab report yet")).toBeVisible();
  } finally {
    await workstation.close();
  }
});
