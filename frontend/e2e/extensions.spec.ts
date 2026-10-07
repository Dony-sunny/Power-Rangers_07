import { test, expect } from "@playwright/test";
const apiBase = process.env.PLAYWRIGHT_API_URL || "http://127.0.0.1:8000";

// Legacy services retain API coverage; main navigation is the approved three roles.
test("coordinator scope and operator account boundaries survive focused navigation", async ({
  page,
  request,
}) => {
  await request.post(`${apiBase}/api/demo/reset`, {
    headers: { "X-Demo-Role": "admin" },
    data: {},
  });
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("control");
  await page
    .getByRole("button", { name: "Plan a departure", exact: true })
    .click();
  await expect(page.getByLabel("Cargo request").locator("option")).toHaveCount(
    3,
  );
  const forbidden = await request.get(
    `${apiBase}/api/cargo/unserved-cargo/compare?vessel_id=vembanad`,
    { headers: { "X-Demo-Role": "control" } },
  );
  expect(forbidden.status()).toBe(404);
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByLabel("Demo operator account")
    .selectOption("demo-pamba-operator");
  await expect(
    page.getByText("Pamba Inland Logistics", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Vessels & availability", exact: true })
    .click();
  await expect(
    page.getByText("MV Pamba", { exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByText("Vembanad Freight", { exact: true })).toHaveCount(
    0,
  );
});
