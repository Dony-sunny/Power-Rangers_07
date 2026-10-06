import { test, expect } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  const response = await request.post("http://127.0.0.1:8000/api/demo/reset", {
    headers: { "X-Demo-Role": "admin" },
    data: {},
  });
  expect(response.ok()).toBeTruthy();
});

test("hero shipment: constraints, pooling, backhaul, booking, delivery, impact", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "A smarter way to move freight." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm hybrid booking" }),
  ).toBeEnabled();
  await page.locator(".rejected-match summary").click();
  await expect(page.getByText(/exceeds demo depth/).first()).toBeVisible();
  await page.getByRole("button", { name: "Optimize", exact: true }).click();
  await expect(page.getByText("53.3% → 92% utilization")).toBeVisible();
  await page.getByRole("button", { name: "Find return" }).click();
  await expect(
    page.getByRole("heading", { name: "coir · 62 t" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Confirm pooled hybrid booking" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Shipment execution" }),
  ).toBeVisible();
  await page.getByLabel("Demo role").selectOption("dispatch");
  for (const state of [
    "scheduled",
    "loading",
    "in transit",
    "unloading",
    "delivered",
  ]) {
    await page
      .getByRole("button", { name: new RegExp(`Confirm ${state}`, "i") })
      .first()
      .click();
    await expect(page.getByRole("status")).toContainText(
      new RegExp(state, "i"),
    );
  }
  await page.getByLabel("Demo role").selectOption("government");
  await expect(page.getByText("138 t", { exact: true }).first()).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/government.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("text intake reviews extracted fields before persistence", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "New cargo request" }).click();
  await page.getByRole("button", { name: "Extract & review" }).click();
  await expect(page.getByLabel("weight_tonnes", { exact: true })).toHaveValue(
    "80",
  );
  await expect(page.getByLabel("origin", { exact: true })).toHaveValue(
    "Kalamassery",
  );
  await page.getByRole("button", { name: "Confirm & create cargo" }).click();
  await expect(
    page.getByRole("heading", { name: "Your cargo requests" }),
  ).toBeVisible();
  await expect(page.getByRole("row")).toHaveCount(5);
});

test("Malayalam demo voice creates actual vessel availability", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByRole("button", { name: "Speak Malayalam to list capacity" })
    .click();
  await page.getByRole("button", { name: "Use demo transcript" }).click();
  await expect(page.getByLabel("capacity_tonnes")).toHaveValue("150");
  await expect(page.getByLabel("origin", { exact: true })).toHaveValue("Kochi");
  await page
    .getByRole("button", { name: "Confirm availability & find cargo" })
    .click();
  await expect(page.getByRole("status")).toContainText("Availability saved");
});

test("all fifteen roles render distinct workspaces without client errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  for (const role of [
    "shipper",
    "dispatch",
    "warehouse",
    "receiver",
    "operator",
    "fleet",
    "captain",
    "terminal",
    "control",
    "finance",
    "compliance",
    "maintenance",
    "network",
    "government",
    "admin",
  ]) {
    await page.getByLabel("Demo role").selectOption(role);
    await expect(page.locator(".loading")).toHaveCount(0);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator(".alert.error")).toHaveCount(0);
  }
  expect(errors).toEqual([]);
});

test("offline map and mobile layout remain usable", async ({ page }) => {
  await page.route("https://**/*", (route) => route.abort());
  await page.goto("/");
  await expect(
    page.getByText("Offline schematic · approximate geography"),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm hybrid booking" }),
  ).toBeEnabled();
  await page.screenshot({
    path: "../docs/screenshots/shipper.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("button", { name: "Open navigation" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../docs/screenshots/mobile.png",
    fullPage: false,
  });
});

test("PDF intake and broker tools use the real services", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Run broker tools" }).click();
  await expect(
    page.getByText(/Deterministic local broker sequence/),
  ).toBeVisible();
  await page.getByRole("button", { name: "New cargo request" }).click();
  await page
    .getByRole("button", { name: "Upload document", exact: true })
    .click();
  await page
    .getByLabel("Cargo document")
    .setInputFiles("../data/demo/sample_purchase_order.pdf");
  await page.getByRole("button", { name: "Extract document" }).click();
  await expect(page.getByLabel("weight_tonnes", { exact: true })).toHaveValue(
    "80",
  );
  await page.getByRole("button", { name: "Confirm & create cargo" }).click();
  await expect(
    page.getByRole("heading", { name: "Your cargo requests" }),
  ).toBeVisible();
});

test("cancellation recovery requires approval and updates the assignment", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Confirm hybrid booking" }).click();
  await page.getByLabel("Demo role").selectOption("dispatch");
  await page
    .getByRole("button", { name: "Simulate vessel cancellation" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Recovery requires your approval" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Approve hybrid recovery" })
    .first()
    .click();
  await expect(page.getByRole("status")).toContainText("Recovery approved");
  await expect(page.locator(".shipment-card").first()).toContainText(
    "MV Pamba",
  );
});

test("scheduled capacity creates a shipment from the service", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Scheduled services", exact: true })
    .click();
  await page.getByRole("button", { name: "Approve capacity booking" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Scheduled capacity confirmed",
  );
  await expect(
    page.getByText("42 / 100 t available on the busiest segment"),
  ).toBeVisible();
});

test("captain can read a cached voyage during an API outage", async ({
  page,
  request,
}) => {
  await request.post("http://127.0.0.1:8000/api/bookings", {
    data: {
      cargo_id: "hero-cargo",
      vessel_id: "vembanad",
      mode: "HYBRID",
      approved: true,
    },
  });
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("captain");
  await expect(
    page.getByRole("heading", { name: "Your assigned voyages" }),
  ).toBeVisible();
  await page.route("**/api/**", (route) => route.abort());
  await page.getByRole("button", { name: "Refresh workspace" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Offline cached voyage view",
  );
  await page
    .getByRole("button", { name: "Confirm Scheduled", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("Reconnect");
});
