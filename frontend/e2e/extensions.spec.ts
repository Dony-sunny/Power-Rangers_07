import { test, expect } from "@playwright/test";

const base = "http://127.0.0.1:8000/api";
test.beforeEach(async ({ request }) => {
  expect(
    (
      await request.post(`${base}/demo/reset`, {
        headers: { "X-Demo-Role": "admin" },
        data: {},
      })
    ).ok(),
  ).toBeTruthy();
});

test("XLSX preview confirms and imports real cargo", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "New cargo request" }).click();
  await page
    .getByRole("button", { name: "Bulk CSV / XLSX", exact: true })
    .click();
  await page
    .getByLabel("Cargo document")
    .setInputFiles("../data/demo/cargo_bulk.xlsx");
  await page.getByRole("button", { name: "Validate spreadsheet" }).click();
  await expect(
    page.getByRole("heading", { name: "Bulk preview · 1 rows" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Import 1 valid rows only" }).click();
  await expect(
    page.getByRole("heading", { name: "Your cargo requests" }),
  ).toBeVisible();
  await expect(page.getByRole("row")).toHaveCount(5);
});

test("terminal collision shows alternate slot", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("admin");
  await page
    .getByRole("button", { name: "Terminal resources", exact: true })
    .click();
  await page
    .getByLabel("Start (India time)", { exact: true })
    .fill("2026-10-08T10:00");
  await page
    .getByLabel("End (India time)", { exact: true })
    .fill("2026-10-08T11:00");
  await page.getByRole("button", { name: "Check and reserve slot" }).click();
  await expect(page.getByRole("status")).toContainText("Resource reserved");
  await page.getByRole("button", { name: "Check and reserve slot" }).click();
  await expect(page.getByRole("alert")).toContainText("Suggested next start");
});

test("recurring departures and fleet plans use actual services", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("control");
  await page
    .getByRole("button", { name: "Scheduled services", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Generate recurring departures" })
    .click();
  await expect(
    page.getByRole("button", { name: "Cancel occurrence" }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel occurrence" }).first().click();
  await expect(page.getByRole("status")).toContainText(
    "One occurrence cancelled",
  );
  await page
    .getByRole("button", { name: "Fleet optimization", exact: true })
    .click();
  await page.getByRole("button", { name: "Optimize fleet assignment" }).click();
  await expect(
    page.getByRole("heading", { name: "Calculated fleet plan" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/fleet.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Approve and revalidate fleet bookings" })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Fleet bookings approved",
  );
});

test("private evidence, QR navigation and OTP verify delivery", async ({
  page,
  request,
}) => {
  const created = await request.post(`${base}/bookings`, {
    data: {
      cargo_id: "hero-cargo",
      vessel_id: "vembanad",
      mode: "HYBRID",
      approved: true,
    },
  });
  expect(created.ok()).toBeTruthy();
  const shipment = (await created.json()).shipment.id;
  for (const status of ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING"]) {
    expect(
      (
        await request.post(`${base}/shipments/${shipment}/transition`, {
          headers: { "X-Demo-Role": "dispatch" },
          data: { status },
        })
      ).ok(),
    ).toBeTruthy();
  }
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("receiver");
  await page
    .getByRole("button", { name: "Evidence & delivery", exact: true })
    .click();
  await page
    .getByLabel("Evidence photo")
    .setInputFiles("../data/demo/scanned_purchase_order.png");
  await page.getByRole("button", { name: "Save photo evidence" }).click();
  await expect(page.locator(".evidence-grid img")).toHaveCount(1);
  await page
    .getByRole("button", { name: "Generate shipment QR label" })
    .click();
  await expect(page.getByAltText("Shipment QR code")).toBeVisible();
  await page
    .getByRole("link", { name: "Open authorized shipment reference" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Authorized QR record" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Request delivery OTP" }).click();
  const code = (await page.getByText(/Demo receiver code:/).innerText()).match(
    /\d{6}/,
  )![0];
  await page.getByLabel("Delivery OTP", { exact: true }).fill(code);
  await page.getByRole("button", { name: "Verify delivery OTP" }).click();
  await expect(page.getByRole("status")).toContainText("verified");
  await page.screenshot({
    path: "../docs/screenshots/evidence.png",
    fullPage: true,
  });
});

test("admin membership and provider fallback work", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("admin");
  await page
    .getByRole("button", { name: "Users & providers", exact: true })
    .click();
  await page
    .getByLabel("Organization name", { exact: true })
    .fill("Browser pilot organization");
  await page
    .getByRole("button", { name: "Create organization", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Organization created");
  await page
    .getByLabel("Member name", { exact: true })
    .fill("Browser pilot member");
  await page.getByRole("button", { name: "Create user", exact: true }).click();
  const row = page.getByRole("row").filter({ hasText: "Browser pilot member" });
  await expect(row).toBeVisible();
  await row.getByRole("combobox").selectOption("dispatch");
  await expect(page.getByRole("status")).toContainText("Role updated");
  await row.getByRole("button", { name: "Disable user" }).click();
  await expect(row.getByText("Disabled", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Run AI connection check" }).click();
  await expect(page.getByRole("status")).toContainText("local fallback");
});

test("guided judge story includes whole-pool recovery and government impact", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("admin");
  await page.getByRole("button", { name: "Judge demo", exact: true }).click();
  await page
    .getByLabel("Include a simulated cancellation and replacement")
    .check();
  for (const stage of [
    "VOICE",
    "CARGO",
    "FEASIBILITY",
    "OPTIMIZATION",
    "BOOK",
    "RECOVERY",
    "START",
    "IMPACT",
  ]) {
    if (["VOICE", "CARGO", "BOOK", "RECOVERY", "START"].includes(stage)) {
      await page
        .getByRole("button", { name: "Preview checkpoint", exact: true })
        .click();
      await page.getByLabel(/I approve the shown/).check();
      await page
        .getByRole("button", { name: "Approve and continue", exact: true })
        .click();
    } else {
      await page
        .getByRole("button", { name: "Run checkpoint", exact: true })
        .click();
    }
    await expect(page.getByRole("status")).toContainText(/Checkpoint/);
  }
  await expect(page.getByText(/Flagship journey completed/)).toBeVisible();
  await expect(page.getByText("138 t", { exact: true }).first()).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/judge.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
