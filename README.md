# Jalayatra AI

**A marketplace for cargo owners and boat operators on Kerala’s waterways.**

Browse and search boat listings, filter by route and capacity, post cargo with its
load details, compare full road/water delivery prices, choose a preferred departure
and follow each booking. Boat operators publish availability and accept delivery
requests; logistics coordinators confirm providers and record delivery progress.

Start with **Post cargo** or the cement sample in **Browse boats**. Choose
**Compare & book** on a boat card, then continue to schedule planning. The full
quote includes connecting trucks and terminal charges. All provider responses
remain simulated in this local prototype.

To try fresh entries, use **Boat operator → My boats → Add a new boat**. Enter
its measurements and route; explicitly select the simulated certificate review
for a bookable demo boat. Then switch to **Cargo owner → Post cargo**, enter a
new load, and choose that boat. Approve the quote and follow the operator and
logistics handoffs. Small loads can be accepted after the operator acknowledges
any estimated sailing shortfall. Each truck and terminal job must be accepted
before confirmation; progress and the final receipt are saved. **My bookings**
provides a way to restart a declined or expired quote.

## Challenge 7: Backwater Cargo Exchange

**Problem:** A builder in Kochi can get a truck price in one call. Getting a barge price takes several calls, without one clear delivered cost or arrival time. Jalayatra brings those decisions into one guided delivery flow.

The supplied IBM × Kerala Government brief asks for a marketplace connecting cargo owners and inland boat operators. Its example is construction materials moving from Kochi to Alappuzha. All five suggested features have working local-prototype flows:

| Brief feature | Where to use it | Implementation evidence |
|---|---|---|
| Cargo posting | Cargo owner → **1. Choose cargo** → Post new cargo; review before saving | [Reviewed intake](frontend/src/components/Intake.tsx), `POST /api/cargo` |
| Boat availability listing | Boat operator → **List boat availability**; review capacity, corridor and exact dates | [Intake](frontend/src/components/Intake.tsx), `POST /api/availability` |
| Matching recommendations | Cargo owner → **2. Compare boats & costs**; ranked feasible boats and visible safety rejections | [Matching](optimization/matching/engine.py), `GET /api/cargo/{id}/matches` |
| Schedule planning | **3. Plan departure** → shared loads → **4. Approve & track** → operator → coordinator | [Planner](backend/services/line_planning.py), [confirmation workflow](backend/services/cargo_lines.py) |
| Cost comparison | **2. Compare boats & costs**; itemized road vs water with connecting trucks | [Whole-trip costs](optimization/multimodal/trip_costs.py), `GET /api/lines/cargo/{id}/advice` |
| Sustainable logistics and increased waterway use | Coordinator → **Delivery & impact**; selected/completed tonnes and labeled full-delivery CO₂ estimates | [Record-derived impact](backend/services/cargo_lines.py), [reproducible fixture](data/demo/measured-results.json) |

Four brief target groups participate through three main workspaces: cargo owners as shippers, boat operators, logistics companies as coordinators, and inland waterway service providers through own-vessel availability and coordinated truck/terminal jobs. Additional dashboards are not needed for this demonstration.

Open **Challenge coverage** in the app to inspect the mapping and download it. The [machine-readable coverage manifest](frontend/src/challenge-coverage.json) gives feature names, behaviors, API paths, source files, verification scenarios and prototype limits. It contains no customer records. [Browser checks](frontend/e2e/demo.spec.ts) verify the connected workflow and visible coverage; [backend checks](tests/integration/test_cargo_lines.py) verify constraints, quotes, shared resources and approvals. These are reproducible evidence, not a guarantee of selection.

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

1. **Demo & settings → Reset demo transactions**, on a disposable demo database.
2. **Cargo owner → 1. Choose cargo:** choose **Compare this cargo** on the preloaded 80 t cement request. In **2. Compare boats & costs**, click **Compare delivery costs**. See ranked boats and MV Deep Blue's visible draft rejection. New cargo uses reviewed text/document/manual intake and reviewed load units.
3. **Continue to schedule planning:** inspect departure/arrival times, **Suggest compatible loads** or select 58 t steel, then **Request dated departure**. The flow moves to **4. Approve & track**. Approve both exact quotes, then use **Open boat operator workspace** for the demo handoff.
4. **Boat operator:** review the combined load and modeled contribution, then **Accept reviewed departure**. Voice availability uses an explicitly selected Malayalam transcript fallback and reviewed exact times.
5. **Logistics coordinator:** use **Simulate remaining provider acceptances**, or respond to each job separately. Four pickup trucks and eight shared terminal jobs are persisted; the shortcut records each acceptance individually. **Confirm delivery bundle** only after every approval.
6. Record shared Scheduled → Loading → In transit → Unloading milestones and each individual door receipt. Open **Delivery & impact** to read selected/completed tonnes and labeled full-delivery CO₂ estimates.
7. For a separate recovery demonstration, withdraw the vessel **before pickup**, find replacements and request new quotes. Owners, the replacement’s own operator and every new job must accept. Use the Pamba operator account for MV Pamba.

Quotes expire within 20 minutes and before cutoff. A declined job releases local
holds; confirmation is idempotent. Cancelling one confirmed member keeps the other
member’s common reservations and accepted price. All provider execution is simulated.

[Five-minute demo](docs/DEMO_SCRIPT.md) · [Nine slides](docs/PRESENTATION_OUTLINE.md) ·
[API](docs/API.md) · [Generated evidence](data/demo/measured-results.json).

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
| Roles | Three main workspaces: cargo owner, boat operator, logistics coordinator. Scoped grants/jobs and own-vessel acceptance; retained legacy models/APIs for compatibility |
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

Current verification commands and evidence are in [Testing](docs/TESTING.md). The focused browser suite covers the three-role quote/provider/receipt journey; legacy services retain backend coverage.

Reset from Demo & settings, or stop the API and run `.venv/Scripts/python.exe scripts/reset_demo.py`. This intentionally deletes previous **demo** records. Seed without deleting records: `.venv/Scripts/python.exe -m data.seed.network`.

## Repository and submission

`backend` contains APIs, SQLAlchemy models, schemas and services. `intelligence`, `feasibility` and `optimization` hold separate reasoning/constraint/solver layers. `data`, `tests`, `scripts`, `frontend` and `docs` provide fixtures and the reproducible artifact. SQLite stays the verified demo database; [PostgreSQL migration readiness](docs/POSTGRESQL_MIGRATION.md) documents the driver, migrations, concurrency and deployment work.

- [Architecture](docs/ARCHITECTURE.md) · [AI & optimization](docs/AI_AND_OPTIMIZATION.md) · [API](docs/API.md)
- [Provenance](docs/DATA_PROVENANCE.md) · [Security](docs/SECURITY.md) · [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Hackathon submission](docs/HACKATHON_SUBMISSION.md) · [9-slide outline](docs/PRESENTATION_OUTLINE.md) · [Judge Q&A](docs/JUDGE_QA.md)
- [Roadmap](docs/FUTURE_ROADMAP.md) · [Measured demo output](data/demo/measured-results.json)
- [Feature audit](docs/FEATURE_AUDIT.md) · [Provider setup](docs/PROVIDER_SETUP.md) · [Publication commands](docs/GITHUB_PUBLICATION.md)

Reproduce the numbers with `.venv/bin/python scripts/generate_measured_results.py` (Windows: `.venv/Scripts/python.exe`). The fixture computes 138 t / 92%, ₹12,240 modeled sailing contribution, ₹15,766.47 delivered-cost difference, 723.66 kg estimated full-delivery CO₂ difference, seven long-haul equivalents and four connecting trips. Rates and factors are synthetic; return opportunities are excluded from contribution and impact.

This is a Git-initialized local repository with reviewed publication commands. Existing `origin` points to `Dony-sunny/keralAI_hack`; this implementation makes local changes and performs no push or hosted deployment. Remote visibility/content was not verified. [Known limitations](docs/KNOWN_LIMITATIONS.md) and the audit identify remaining partial/production requirements.
