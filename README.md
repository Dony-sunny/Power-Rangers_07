# Jalayatra AI

**Kerala's Agentic Inland Freight Exchange & Multimodal Logistics Operating System**

A working React + FastAPI freight prototype: text, scanned documents or XLSX become reviewed cargo; Malayalam-friendly operator intake becomes capacity; deterministic feasibility, pooling, fleet assignment, recurring services and terminal resources lead to approved bookings, evidence, recovery and measured impact.

![Shipper transport planner](docs/screenshots/shipper.png)

## Start locally

Requirements: Python 3.12+, Node 22+ (tested with Node 24), npm. Internet is needed to install dependencies once. No AI/API key is required for the demo.

Windows PowerShell, from this repository:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
python scripts/dev.py
```

Linux/macOS:

```bash
bash scripts/setup.sh
python3 scripts/dev.py
```

Open **http://127.0.0.1:5173**. Interactive API documentation: **http://127.0.0.1:8000/docs**. Startup seeds an empty database automatically. Stop the helper with Ctrl+C. Both services bind to localhost.

If starting separately:

```powershell
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal: `cd frontend` then `npm run dev`. For a production frontend bundle, run `npm run build` in `frontend`. This repository is a local prototype, not a production deployment.

## Reproduce the flagship demo

For the guided version, switch to **Platform admin → Judge demo**. Preview each checkpoint, explicitly approve intake/booking/departure, and optionally include whole-pool cancellation recovery. It calls the same services as the manual workspaces. [Complete feature audit](docs/FEATURE_AUDIT.md) records all 56 master sections, every role feature and continuation phases with source references.

1. Switch to **Platform admin** and click **Reset demo transactions**.
2. Switch to **Vessel operator**, select **Voice availability**, click **Use demo transcript**, review the 150 t Kochi → Alappuzha extraction and confirm the suggested operating window. This is a disclosed transcript fallback, not live speech recognition.
3. Switch to **Shipper procurement**. The 80 t cement request is preloaded. Use **New cargo request** for text, text/scanned PDF, PNG/JPEG, manual or CSV/XLSX intake. Run `.venv/Scripts/python.exe scripts/make_demo_documents.py` to generate current-dated synthetic samples. Bulk import previews valid/invalid rows before approval.
4. Expand **MV Deep Blue**: its attractive commercial fit cannot override the draft failure. MV Vembanad passes the configured physical constraints.
5. Inspect road, water and hybrid. Direct water is unavailable for a door pickup; hybrid includes the connecting truck. With terminal-to-terminal cargo, water is available. Urgent cargo can cause road to win.
6. Click **Optimize**: 80 + 58 = **138 t**, **92%** of the 150 t vessel. Click **Find return**: a **62 t coir** load fits the return window.
7. Click **Confirm pooled hybrid booking**. Both cargo records receive bookings, shipments, invoice drafts and impact records in one transaction.
8. Switch to **Shipper dispatch** or **Captain**. Advance each shipment through scheduled → loading → in transit → unloading → delivered. Required last-mile cargo has an additional last-mile milestone.
9. Switch to **Government analytics**. **138 t** selected for water is derived from those two bookings. Completed tonnage increases only as shipments finish. No transaction means zero shifted cargo, savings or avoided CO₂.
10. For recovery, reset and book the hero or pool. Dispatch can simulate eight disruption types, inspect cost/ETA changes and approve an individual or whole-pool replacement. Recovery is pre-departure. For verified prototype delivery, the consignee requests and enters the local OTP at unloading; old milestone-only demo deliveries remain unverified.

Full timing and A–F scenario instructions: [Demo script](docs/DEMO_SCRIPT.md).

## What is implemented

| Area | Working behavior |
|---|---|
| Intake | Manual/text; text PDF first then actual local OCR for scanned PDF/PNG/JPEG; XLSX/CSV validation/template/errors and atomic valid-only import; Malayalam/mixed voice/text with configurable STT and explicit fallback |
| Feasibility | Dijkstra route graph; draft/safety margin, air draft, width, locks, deadlines, terminal slots/capabilities, cargo compatibility, maintenance, verified registration/insurance expiry |
| Matching | Feasible candidates ranked with configurable profiles, score factors and readable rejection evidence |
| Procurement | Multiple computed quotes, complete road/water/hybrid cost lines, ETA/SLA, transparent carbon factors and deterministic booking risk |
| Optimization | CP-SAT pooling and multi-vessel assignment with five objectives; backhaul/terminal selection; recurring patterns, segment occupancy, reservations and capacity contracts |
| Execution | Atomic bookings/states; simulated tracking; berth/equipment/storage/gate collision checks; truck/crew/loading records; private photos, authorized opaque QR labels, local prototype OTP and documents |
| Recovery | Eight pre-departure disruptions; later/service/vessel/terminal/road alternatives; cost/ETA deltas and atomic whole-pool approval |
| Intelligence | Booking-derived impact, corridor actual milestones, rate sample bounds, typed failed demand, historical modal-shift upload, reviewed/photo navigation observations, activation and flood decision support |
| Roles | 15 workspaces; organization/user create/change/disable, payment/disputes, provider diagnostics, signed stored identities, backend scope checks and financial redaction |
| Reliability | Offline schematic map, optional OSM tiles, no mandatory external AI, seed/reset commands, unit/integration/browser tests, CI |

Advanced role features are explicitly mapped to implemented behavior or architecture in [Workspace coverage](docs/WORKSPACE_COVERAGE.md); roadmap integrations are not represented as connected.

## AI and operational truth

Default `AI_PROVIDER=local` uses deterministic extraction and tool orchestration, **not ML**. An optional chat-completions-compatible LLM can extract structured fields, interpret image documents and select bounded broker tools. Pydantic validates all extracted fields. The LLM never supplies navigation values, totals or safety overrides. OR-Tools and hard constraints remain separate.

Copy `.env.example` to `.env` only if customizing configuration. [Provider setup](docs/PROVIDER_SETUP.md) gives exact LLM/STT/GPS/weather contracts and a read-only smoke command. Timeouts, invalid responses and outages degrade to disclosed fallback. No external LLM or Malayalam speech credential was available for real validation here.

**Demo identity is intentionally switchable.** Do not expose demo mode publicly. Outside demo mode, the backend requires signed, expiring bearer identities and a strong `AUTH_SECRET`; production identity provisioning/SSO is roadmap work. See [Security](docs/SECURITY.md).

## Tests and reset

```powershell
.venv/Scripts/python.exe -m pytest -p no:cacheprovider
cd frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser tests require the two local services and reset the demo database. If using a workspace browser installation, set `PLAYWRIGHT_BROWSERS_PATH` to its path. Backend tests use isolated in-memory databases. See [Testing](docs/TESTING.md).

Verified continuation gate: **93 backend tests**, **15 browser tests**, and the production build pass. New checks include actual scanned-PDF OCR, recurring rollback, fleet compatibility, terminal collisions and pooled equipment, private evidence/QR/OTP, administration and guided recovery. Tests establish the documented prototype behavior; the audit retains production and secondary-feature gaps.

Reset from the admin UI, or stop the API and run `.venv/Scripts/python.exe scripts/reset_demo.py`. This intentionally deletes previous **demo** records. Seed without deleting records: `.venv/Scripts/python.exe -m data.seed.network`.

## Repository and submission

`backend` contains APIs, SQLAlchemy models, schemas and services. `intelligence`, `feasibility` and `optimization` hold separate reasoning/constraint/solver layers. `data`, `tests`, `scripts`, `frontend` and `docs` provide fixtures and the reproducible artifact. SQLite stays the verified demo database; [PostgreSQL migration readiness](docs/POSTGRESQL_MIGRATION.md) documents the driver, migrations, concurrency and deployment work.

- [Architecture](docs/ARCHITECTURE.md) · [AI & optimization](docs/AI_AND_OPTIMIZATION.md) · [API](docs/API.md)
- [Provenance](docs/DATA_PROVENANCE.md) · [Security](docs/SECURITY.md) · [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Hackathon submission](docs/HACKATHON_SUBMISSION.md) · [9-slide outline](docs/PRESENTATION_OUTLINE.md) · [Judge Q&A](docs/JUDGE_QA.md)
- [Roadmap](docs/FUTURE_ROADMAP.md) · [Measured demo output](data/demo/measured-results.json)
- [Feature audit](docs/FEATURE_AUDIT.md) · [Provider setup](docs/PROVIDER_SETUP.md) · [Publication commands](docs/GITHUB_PUBLICATION.md)

Reproduce the numbers with `.venv/Scripts/python.exe scripts/generate_measured_results.py`. The hero computes 138 t/92% utilization, ₹27,857.40 pooled cost difference, 723.66 kg estimated CO₂ difference and seven equivalent long-haul truck movements. All rates/emissions/navigation inputs are synthetic assumptions, and a 62 t return **opportunity** counts as avoided empty travel only when booked.

This is a Git-initialized local repository with reviewed publication commands. Existing `origin` points to `Dony-sunny/keralAI_hack`; this continuation made local commits and performed no push or hosted deployment. Remote visibility/content was not verified. [Known limitations](docs/KNOWN_LIMITATIONS.md) and the audit identify remaining partial/production requirements.
