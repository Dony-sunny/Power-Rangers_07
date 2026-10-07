import { test, expect, type Page } from "@playwright/test";
const apiBase = process.env.PLAYWRIGHT_API_URL || "http://127.0.0.1:8000";

test.beforeEach(async ({ request }) => {
  const response = await request.post(`${apiBase}/api/demo/reset`, {
    headers: { "X-Demo-Role": "admin" },
    data: {},
  });
  expect(response.ok()).toBeTruthy();
});

async function proposal(page: Page) {
  await page.goto("/");
  await page
    .locator(".market-boat-card")
    .filter({ hasText: "MV Vembanad" })
    .getByRole("button", { name: "Compare & book" })
    .first()
    .click();
  await page
    .getByRole("button", { name: "Compare delivery costs", exact: true })
    .click();
  await expect(
    page.getByText("4 truck trips", { exact: false }).first(),
  ).toBeVisible();
  await expect(
    page.locator(".boat-match").filter({ hasText: "MV Vembanad" }),
  ).toBeVisible();
  await expect(page.locator(".rejected-boats")).toContainText("MV Deep Blue");
  await page
    .getByRole("button", { name: "Continue to schedule planning" })
    .click();
  await expect(page.locator(".schedule-summary")).toContainText(
    "Water departure",
  );
  await page.getByLabel(/Steel · 58 t/).check();
  await page.getByRole("button", { name: "Request dated departure" }).click();
  await expect(page.getByTestId("departure")).toHaveCount(1);
}

async function approve(page: Page) {
  const cards = page.getByTestId("departure");
  await cards
    .getByRole("button", { name: "Approve this quote", exact: true })
    .first()
    .click();
  await expect(
    cards.getByRole("button", { name: "Quote approved", exact: true }),
  ).toHaveCount(1);
  await cards
    .getByRole("button", { name: "Approve this quote", exact: true })
    .click();
  await expect(
    cards.getByRole("button", { name: "Quote approved", exact: true }),
  ).toHaveCount(2);
}

test("three-role journey locks price, accepts operators/jobs and records individual receipts", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await proposal(page);
  await expect(
    page.getByRole("button", { name: "Confirm delivery bundle" }),
  ).toBeDisabled();
  await approve(page);
  await page
    .getByRole("button", { name: "Open boat operator workspace" })
    .click();
  await expect(
    page.getByText("Accepted delivery revenue covers modeled voyage costs.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Accept reviewed departure" }).click();
  await expect(page.getByText(/Operator accepted version 1/)).toBeVisible();
  await page
    .getByRole("button", { name: "Open logistics coordinator workspace" })
    .click();
  const acceptJobs = page.getByRole("button", {
    name: /^Simulate accept /,
  });
  await expect(acceptJobs).toHaveCount(12);
  await page
    .getByRole("button", { name: "Simulate remaining provider acceptances" })
    .click();
  await expect(acceptJobs).toHaveCount(0);
  const persisted = await (
    await request.get(`${apiBase}/api/lines`, {
      headers: { "X-Demo-Role": "control" },
    })
  ).json();
  expect(persisted.departures[0].jobs).toHaveLength(12);
  expect(
    persisted.departures[0].jobs.every(
      (job: { status: string }) => job.status === "ACCEPTED",
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Confirm delivery bundle" }).click();
  await expect(page.getByText(/Customer reference booking-/)).toHaveCount(2);
  for (const state of ["Scheduled", "Loading", "In transit", "Unloading"]) {
    await page
      .getByRole("button", { name: "Record " + state, exact: true })
      .click();
  }
  for (const cargo of ["hero-cargo", "pool-cargo"]) {
    await page.getByLabel("Receiver name " + cargo).fill("Alappuzha builder");
    await page
      .locator("form")
      .filter({ has: page.getByLabel("Receiver name " + cargo) })
      .getByRole("button", { name: "Record door receipt" })
      .click();
    await expect(page.getByLabel("Receiver name " + cargo)).toHaveCount(0);
  }
  await page
    .getByRole("button", { name: "Delivery & impact", exact: true })
    .click();
  await expect(
    page.locator(".stat").filter({ hasText: "Completed water tonnes" }),
  ).toContainText("138 t");
  await expect(page.getByText(/Full delivery tonne-km estimate/)).toBeVisible();
  await page.getByLabel("Demo role").selectOption("shipper");
  await expect(page.getByText(/Invoice draft invoice-/)).toHaveCount(2);
  expect(errors).toEqual([]);
});

test("marketplace search, filters and mobile booking remain usable", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Demo role").locator("option")).toHaveCount(3);
  await page.getByLabel("Search boats or routes").fill("Vembanad");
  await page.getByRole("button", { name: "Search marketplace" }).click();
  await expect(page.locator(".market-boat-card").first()).toBeVisible();
  await page.getByRole("button", { name: "Clear all filters" }).click();
  await page.getByLabel("Minimum boat capacity").selectOption("150");
  await expect(page.locator(".market-boat-card").first()).toBeVisible();
  await page.getByRole("button", { name: "Clear all filters" }).click();
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 2,
    ),
  ).toBeTruthy();
  await page
    .locator(".market-boat-card")
    .filter({ hasText: "MV Vembanad" })
    .getByRole("button", { name: "Compare & book" })
    .first()
    .click();
  await expect(
    page.getByRole("button", { name: "Compare delivery costs", exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("navigation", { name: "Delivery steps" })
      .getByRole("button", { name: /Plan departure/ }),
  ).toBeDisabled();
});

test("marketplace cargo posting saves a reviewed load ready for scheduling", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Post cargo", exact: true }).click();
  await page.getByRole("button", { name: "Use cement sample" }).click();
  await page.getByRole("button", { name: "Review cargo", exact: true }).click();
  await page
    .getByRole("button", { name: "Confirm & post cargo", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Cargo posted");
  const postedId = await page
    .getByLabel("Choose cargo for matching")
    .inputValue();
  expect(postedId).not.toBe("hero-cargo");
  const profile = await (
    await request.get(`${apiBase}/api/lines/cargo/${postedId}/profile`)
  ).json();
  expect(profile.profile.pieces).toBe(1600);
  await page
    .locator(".market-boat-card")
    .filter({ hasText: "MV Vembanad" })
    .getByRole("button", { name: "Compare & book" })
    .first()
    .click();
  await page
    .getByRole("button", { name: "Compare delivery costs", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Continue to schedule planning" }),
  ).toBeVisible();
});

test("fresh boat and one-tonne cargo complete individual approvals and delivery", async ({
  page,
  request,
}) => {
  test.setTimeout(120000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByLabel("Demo operator account")
    .selectOption("demo-pamba-operator");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "My boats", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Add a new boat", exact: true })
    .click();
  await page
    .getByLabel("Boat name", { exact: true })
    .fill("Fresh small cargo boat");
  for (const [label, value] of [
    ["Maximum capacity (tonnes)", "100"],
    ["Cargo volume (m³)", "160"],
    ["Boat length (m)", "38"],
    ["Boat width (m)", "7.5"],
    ["Loaded draft (m)", "1.3"],
    ["Air draft (m)", "3.8"],
    ["Boat rate (₹ / tonne-km)", "3"],
  ])
    await page.getByLabel(label, { exact: true }).fill(value);
  await page.getByLabel("Route from", { exact: true }).selectOption("Maradu");
  await page.getByLabel("Route to", { exact: true }).selectOption("Alappuzha");
  const available = await page
    .getByLabel("Available from (IST)", { exact: true })
    .inputValue();
  await page
    .getByLabel(/Use simulated registration and insurance review/)
    .check();
  await page.getByRole("button", { name: "Review boat", exact: true }).click();
  await page
    .getByRole("button", { name: "Register & publish boat", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Boat registered");
  const fleet = await (
    await request.get(`${apiBase}/api/workspace`, {
      headers: {
        "X-Demo-Role": "operator",
        "X-Demo-User": "demo-pamba-operator",
      },
    })
  ).json();
  const boat = fleet.vessels.find(
    (v: { name: string }) => v.name === "Fresh small cargo boat",
  );
  expect(boat.compliance_status).toBe("PASS");
  expect(
    fleet.availability.filter(
      (a: { vessel_id: string }) => a.vessel_id === boat.id,
    ),
  ).toHaveLength(1);
  // Leave the other operator selected to verify the booking handoff picks the
  // account which actually owns this newly registered boat.
  await page.getByLabel("Demo operator account").selectOption("demo-operator");
  await page.getByLabel("Demo role").selectOption("shipper");
  await page.getByRole("button", { name: "Post cargo", exact: true }).click();
  await page.getByLabel("Goods to transport").selectOption("cement");
  await page.getByLabel("Total weight (tonnes)").fill("1");
  await page.getByLabel("Total volume (m³)").fill("2");
  await page
    .getByLabel("Pickup location", { exact: true })
    .selectOption("Kalamassery");
  await page
    .getByLabel("Delivery location", { exact: true })
    .selectOption("Alappuzha");
  await page
    .getByLabel("Ready for pickup", { exact: true })
    .fill(available.slice(0, 10) + "T09:00");
  const deadline = new Date(
    new Date(available + "+05:30").getTime() + 2 * 86400000,
  );
  await page
    .getByLabel("Deliver by", { exact: true })
    .fill(
      deadline
        .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
        .replace(" ", "T")
        .slice(0, 16),
    );
  await expect(page.getByLabel("Number of pieces")).toHaveValue("20");
  await page.getByLabel("Largest piece length (m)").fill("0.6");
  await page.getByLabel("Largest piece width (m)").fill("0.4");
  await page.getByLabel("Largest piece height (m)").fill("0.2");
  await page.getByLabel("Allow compatible cargo to share the boat").uncheck();
  await page.getByRole("button", { name: "Review cargo", exact: true }).click();
  await page
    .getByRole("button", { name: "Confirm & post cargo", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Cargo posted");
  const cargoId = await page
    .getByLabel("Choose cargo for matching")
    .inputValue();
  expect(cargoId).not.toBe("hero-cargo");
  await page
    .locator(".market-boat-card")
    .filter({ hasText: "Fresh small cargo boat" })
    .getByRole("button", { name: "Compare & book" })
    .click();
  await expect(
    page.getByRole("button", { name: "Continue to schedule planning" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Continue to schedule planning" })
    .click();
  await page.getByRole("button", { name: "Request dated departure" }).click();
  await expect(page.getByTestId("departure")).toHaveCount(1);
  await page
    .getByRole("button", { name: "Approve this quote", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Open boat operator workspace" })
    .click();
  await expect(page.getByLabel("Demo operator account")).toHaveValue(
    "demo-pamba-operator",
  );
  await expect(page.getByTestId("departure")).toContainText(
    "Fresh small cargo boat",
  );
  await expect(
    page.getByRole("button", { name: "Accept reviewed departure" }),
  ).toBeDisabled();
  await page
    .getByLabel(
      /I accept the approved price despite the estimated sailing shortfall/,
    )
    .check();
  await page.getByRole("button", { name: "Accept reviewed departure" }).click();
  await expect(page.getByText(/Operator accepted version 1/)).toBeVisible();
  await page
    .getByRole("button", { name: "Open logistics coordinator workspace" })
    .click();
  const accepts = page.getByRole("button", { name: /^Simulate accept / });
  await expect(accepts.first()).toBeVisible();
  const count = await accepts.count();
  expect(count).toBeGreaterThan(2);
  await expect(
    page.getByRole("button", { name: "Confirm delivery bundle" }),
  ).toBeDisabled();
  for (let remaining = count; remaining > 0; remaining--) {
    await accepts.first().click();
    await expect(accepts).toHaveCount(remaining - 1);
  }
  const approval = await (
    await request.get(`${apiBase}/api/lines`, {
      headers: { "X-Demo-Role": "control" },
    })
  ).json();
  expect(approval.departures[0].vessel_id).toBe(boat.id);
  expect(approval.departures[0].operator_accepted).toBeTruthy();
  expect(
    approval.departures[0].jobs.every(
      (j: { status: string }) => j.status === "ACCEPTED",
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Confirm delivery bundle" }).click();
  await expect(page.getByText(/Customer reference booking-/)).toHaveCount(1);
  for (const state of ["Scheduled", "Loading", "In transit", "Unloading"]) {
    await page
      .getByRole("button", { name: "Record " + state, exact: true })
      .click();
  }
  await page
    .getByLabel("Receiver name " + cargoId)
    .fill("Fresh shipment receiver");
  await page.getByRole("button", { name: "Record door receipt" }).click();
  await expect(page.getByLabel("Receiver name " + cargoId)).toHaveCount(0);
  const delivered = await (await request.get(`${apiBase}/api/lines`)).json();
  expect(delivered.departures[0].status).toBe("COMPLETED");
  expect(delivered.departures[0].members[0].receipt.quantity_tonnes).toBe(1);
  await page.getByLabel("Demo role").selectOption("shipper");
  await page.reload();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "My bookings", exact: true })
    .click();
  await expect(page.getByTestId("departure")).toContainText(
    "Fresh small cargo boat",
  );
  await expect(page.getByText(/Invoice draft invoice-/)).toHaveCount(1);
  expect(errors).toEqual([]);
});

test("operator availability uses an explicitly chosen Malayalam transcript", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "List your boat", exact: true })
    .click();
  await page.getByRole("button", { name: "Voice / transcript" }).click();
  await page.getByRole("button", { name: "Use demo transcript" }).click();
  await expect(page.getByLabel("capacity_tonnes")).toHaveValue("150");
  await expect(page.getByLabel("origin", { exact: true })).toHaveValue("Kochi");
  await page
    .getByRole("button", { name: "Confirm availability & find cargo" })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Boat availability published",
  );
});

test("a declined handling job releases the proposal and blocks confirmation", async ({
  page,
}) => {
  await proposal(page);
  await page.getByLabel("Demo role").selectOption("control");
  await page
    .getByRole("button", { name: /^Simulate decline / })
    .first()
    .click();
  await expect(
    page
      .getByTestId("departure")
      .getByText("Declined", { exact: true })
      .first(),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm delivery bundle" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: /^Simulate accept / }),
  ).toHaveCount(0);
  await page.getByLabel("Demo role").selectOption("shipper");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "My bookings", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Find a boat for Cement · 80 t" })
    .click();
  await expect(page.getByLabel("Choose cargo for matching")).toHaveValue(
    "hero-cargo",
  );
  await page
    .locator(".market-boat-card")
    .filter({ hasText: "MV Vembanad" })
    .getByRole("button", { name: "Compare & book" })
    .first()
    .click();
  await expect(
    page.getByRole("button", { name: "Continue to schedule planning" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Continue to schedule planning" })
    .click();
  await page.getByRole("button", { name: "Request dated departure" }).click();
  await expect(
    page.getByRole("button", { name: "Approve this quote", exact: true }),
  ).toHaveCount(1);
});

test("pre-pickup replacement needs fresh owner quotes and its own operator", async ({
  page,
  request,
}) => {
  const response = await request.post(`${apiBase}/api/lines/proposals`, {
    data: { cargo_ids: ["hero-cargo", "pool-cargo"], vessel_id: "vembanad" },
  });
  expect(response.status()).toBe(201);
  const original = await response.json();
  for (const member of original.members)
    expect(
      (
        await request.post(
          `${apiBase}/api/lines/quotes/${member.quote.id}/approve`,
        )
      ).ok(),
    ).toBeTruthy();
  expect(
    (
      await request.post(
        `${apiBase}/api/lines/${original.id}/operator-response`,
        {
          headers: { "X-Demo-Role": "operator" },
          data: { version: 1, accept: true },
        },
      )
    ).ok(),
  ).toBeTruthy();
  for (const job of original.jobs)
    expect(
      (
        await request.post(`${apiBase}/api/lines/jobs/${job.id}/response`, {
          headers: { "X-Demo-Role": "control" },
          data: { status: "ACCEPTED" },
        })
      ).ok(),
    ).toBeTruthy();
  expect(
    (await request.post(`${apiBase}/api/lines/${original.id}/confirm`)).ok(),
  ).toBeTruthy();
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("control");
  await page.getByText("Booking details & changes", { exact: true }).click();
  await page
    .getByRole("button", { name: "Simulate pre-pickup vessel withdrawal" })
    .click();
  await page
    .getByRole("button", { name: "Find replacement departures" })
    .click();
  await page
    .getByRole("button", { name: "Request replacement quotes" })
    .click();
  await expect(page.getByTestId("departure")).toHaveCount(2);
  await page.getByLabel("Demo role").selectOption("shipper");
  await expect(
    page.getByRole("button", { name: "Approve this quote", exact: true }),
  ).toHaveCount(2);
  await approve(page);
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByLabel("Demo operator account")
    .selectOption("demo-pamba-operator");
  await expect(
    page.getByRole("button", { name: "Accept reviewed departure" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Accept reviewed departure" }).click();
  await expect(page.getByText(/Operator accepted version 1/)).toBeVisible();
  await page.getByLabel("Demo role").selectOption("control");
  const acceptJobs = page.getByRole("button", { name: /^Simulate accept / });
  await expect(acceptJobs).toHaveCount(12);
  for (let count = 12; count > 0; count--) {
    await acceptJobs.first().click();
    await expect(acceptJobs).toHaveCount(count - 1);
  }
  await page.getByRole("button", { name: "Confirm delivery bundle" }).click();
  await page
    .getByRole("button", { name: "Delivery & impact", exact: true })
    .click();
  await expect(
    page.locator(".stat").filter({ hasText: "Selected water tonnes" }),
  ).toContainText("138 t");
  await expect(page.getByText(/Invoice draft.*VOID/)).toHaveCount(2);
});

test("boat acceptance explains its blocker and offers the correct demo handoff", async ({
  page,
}) => {
  await proposal(page);
  await page.getByLabel("Demo role").selectOption("operator");
  await expect(
    page.getByText(
      "Acceptance unlocks after every cargo owner approves their quote.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Accept reviewed departure" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Open cargo owner workspace" })
    .click();
  await expect(
    page.getByRole("button", { name: "Approve this quote", exact: true }),
  ).toHaveCount(2);
});

test("challenge coverage identifies all five brief features, impact and verification sources", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Challenge coverage", exact: true })
    .click();
  for (const name of [
    "Cargo posting",
    "Boat availability listing",
    "Matching recommendations",
    "Schedule planning",
    "Cost comparison",
    "Sustainable logistics and increased waterway use",
  ])
    await expect(
      page.getByRole("heading", { name, exact: true }),
    ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Four target user groups, three main workspaces",
    }),
  ).toBeVisible();
  await page
    .getByText("Source, API and verification scenarios", { exact: true })
    .first()
    .click();
  await expect(
    page.getByText("POST /api/cargo", { exact: true }),
  ).toBeVisible();
  const downloadEvent = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download coverage evidence" })
    .click();
  expect((await downloadEvent).suggestedFilename()).toBe(
    "Jalayatra-challenge-coverage.json",
  );
});

test("preferred departure recalculates dates and recovers from an impossible time", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page
    .locator(".market-boat-card")
    .filter({ hasText: "MV Vembanad" })
    .getByRole("button", { name: "Compare & book" })
    .first()
    .click();
  await page
    .getByRole("button", { name: "Continue to schedule planning" })
    .click();
  const baseline = await (
    await request.get(
      `${apiBase}/api/lines/cargo/hero-cargo/advice?vessel_id=vembanad`,
    )
  ).json();
  const preferred = new Date(
    new Date(baseline.water.departure).getTime() + 30 * 60000,
  )
    .toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" })
    .replace(" ", "T")
    .slice(0, 16);
  await page.getByLabel("Preferred departure (IST)").fill(preferred);
  await expect(
    page.getByRole("button", { name: "Request dated departure" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Update departure" }).click();
  await expect(
    page.getByRole("button", { name: "Request dated departure" }),
  ).toBeEnabled();
  await page.getByLabel("Preferred departure (IST)").fill("2030-01-01T12:00");
  await page.getByRole("button", { name: "Update departure" }).click();
  await expect(
    page.getByRole("heading", { name: "This departure is unavailable" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Find earliest available departure" })
    .click();
  await expect(page.getByLabel("Preferred departure (IST)")).toHaveValue("");
  await expect(
    page.getByRole("button", { name: "Request dated departure" }),
  ).toBeEnabled();
});

test("manual boat listing publishes a persisted availability window", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "List your boat", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Review availability", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Publish boat availability", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Boat availability published",
  );
  await expect(
    page.getByRole("heading", { name: "My boat listings", exact: true }),
  ).toBeVisible();
  const workspace = await (
    await request.get(`${apiBase}/api/workspace`, {
      headers: { "X-Demo-Role": "operator" },
    })
  ).json();
  expect(
    workspace.availability.some((a: { id: string }) =>
      a.id.startsWith("availability-"),
    ),
  ).toBeTruthy();
});

test("operator edits a listing, pauses it and republishes the same window", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "My boats", exact: true })
    .click();
  const original = await (
    await request.get(`${apiBase}/api/workspace`, {
      headers: { "X-Demo-Role": "operator" },
    })
  ).json();
  const listing = original.availability.find(
    (a: { vessel_id: string; destination: string }) =>
      a.vessel_id === "vembanad" && a.destination === "Alappuzha",
  );
  const window = page
    .locator(".operator-boat-card")
    .filter({ hasText: "MV Vembanad" })
    .getByTestId("operator-window")
    .filter({ hasText: "Alappuzha" })
    .first();
  await window
    .getByRole("button", { name: "Edit availability", exact: true })
    .click();
  await page
    .getByLabel("Available capacity (tonnes)", { exact: true })
    .fill("120");
  await page
    .getByRole("button", { name: "Review availability", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Save availability changes", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Boat availability updated",
  );
  await expect(window).toContainText("120 t available");
  const edited = await (
    await request.get(`${apiBase}/api/workspace`, {
      headers: { "X-Demo-Role": "operator" },
    })
  ).json();
  expect(edited.availability).toHaveLength(original.availability.length);
  expect(
    edited.availability.find((a: { id: string }) => a.id === listing.id)
      .capacity_tonnes,
  ).toBe(120);
  await window
    .getByRole("button", { name: "Pause listing", exact: true })
    .click();
  await expect(window.getByText("Paused", { exact: true })).toBeVisible();
  await page.getByLabel("Demo role").selectOption("shipper");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "Browse boats", exact: true })
    .click();
  await expect(
    page.locator(".market-boat-card").filter({ hasText: "MV Vembanad" }),
  ).toHaveCount(0);
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "My boats", exact: true })
    .click();
  await window
    .getByRole("button", { name: "Publish listing", exact: true })
    .click();
  await expect(window.getByText("Published", { exact: true })).toBeVisible();
});

test("operator discovers compatible cargo and retains clear mobile actions", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("operator");
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "Find cargo", exact: true })
    .click();
  await page.getByLabel("Find cargo for boat").selectOption("vembanad");
  await expect(
    page.locator(".operator-demand-card").filter({ hasText: "Cement · 80 t" }),
  ).toBeVisible();
  await page.getByLabel("Search cargo or routes").fill("Steel");
  await page.getByRole("button", { name: "Search marketplace" }).click();
  await expect(page.locator(".operator-demand-card")).toHaveCount(1);
  await expect(page.locator(".operator-demand-card")).toContainText("Steel");
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 2,
    ),
  ).toBeTruthy();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "List your boat", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Review availability", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 2,
    ),
  ).toBeTruthy();
});

test("logistics demo loader adds persisted stages and provider actions remain usable", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page.getByLabel("Demo role").selectOption("control");
  await page
    .locator(".logistics-hero")
    .getByRole("button", { name: "Add demo deliveries", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Sample deliveries added",
  );
  await expect(page.getByTestId("departure")).toHaveCount(3);
  await expect(page.getByTestId("departure").first()).toContainText(
    "Demo Kuttanad Cargo",
  );
  await page
    .getByLabel("Filter logistics deliveries")
    .selectOption("completed");
  await expect(page.getByTestId("departure")).toHaveCount(1);
  await expect(page.getByTestId("departure")).toContainText(
    "Demo Pamba Freight",
  );
  await page.getByLabel("Filter logistics deliveries").selectOption("all");
  await page.getByLabel("Search deliveries or routes").fill("Demo Kuttanad");
  await page.getByRole("button", { name: "Search marketplace" }).click();
  await expect(page.getByTestId("departure")).toHaveCount(1);
  await page
    .getByRole("button", { name: "Simulate remaining provider acceptances" })
    .click();
  await expect(
    page.getByRole("button", { name: "Confirm delivery bundle" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Confirm delivery bundle" }).click();
  await expect(
    page.getByRole("button", { name: "Record Scheduled", exact: true }),
  ).toBeVisible();
  const before = (
    await (
      await request.get(`${apiBase}/api/lines`, {
        headers: { "X-Demo-Role": "control" },
      })
    ).json()
  ).departures.length;
  await page
    .locator(".logistics-hero")
    .getByRole("button", { name: "Add demo deliveries", exact: true })
    .click();
  const after = (
    await (
      await request.get(`${apiBase}/api/lines`, {
        headers: { "X-Demo-Role": "control" },
      })
    ).json()
  ).departures.length;
  expect(after).toBe(before);
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 2,
    ),
  ).toBeTruthy();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: "Delivery & impact", exact: true })
    .click();
  await expect(
    page.locator(".stat").filter({ hasText: "Completed water tonnes" }),
  ).toContainText("138 t");
});

test("boat browsing shows matching listings without unsuitable messages", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".market-results-note")).toContainText(
    "boats pass the cargo",
  );
  await expect(
    page.getByText("Not suitable for selected cargo", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.locator(".market-boat-card").filter({ hasText: "MV Deep Blue" }),
  ).toHaveCount(0);
  await expect(
    page
      .locator(".market-boat-card")
      .filter({ hasText: "MV Vembanad" })
      .getByRole("button", { name: "Compare & book" }),
  ).toBeEnabled();
});
