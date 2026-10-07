# Testing

Backend tests use a fresh seeded, foreign-key-enabled in-memory SQLite database for every test. They do not mutate the running demo. FastAPI integration tests go through actual schemas, RBAC, services and persistence.

Final local verification on 7 October 2026: **93 backend tests passed** (27.10 s), **15 Chromium end-to-end tests passed** (37.3 s), and the TypeScript/Vite production build passed. The preserved pre-edit baseline was 41 backend / 9 browser / passing build. A Starlette/httpx deprecation notice and Node color warning remain third-party non-failing warnings.

```powershell
.venv/Scripts/python.exe -m pytest -p no:cacheprovider
cd frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

Start both services before browser tests. Browser tests run serially and reset the **demo database** before each case. On this workspace, Chromium is installed under `.runtime/browsers`; use `$env:PLAYWRIGHT_BROWSERS_PATH = 'C:\keralAI hackathon\.runtime\browsers'` if using that installation. Else normal Playwright installation uses its standard cache.

## Critical coverage

| Requirement | Coverage |
|---|---|
| Cargo schema and missing fields | `test_intake.py` validates explicit weight/volume/route/time extraction and null missing fields |
| Voice schema | Native Malayalam + provided transliteration; missing exact availability windows |
| Physical failures | Parameterized overweight, volume, dangerous cargo, cold chain, draft, bridge, beam, maintenance, terminal equipment and expired insurance |
| Feasibility before ranking | Deep Blue excluded; repeat fixture ranking is identical |
| Pool capacity/compatibility | 138 t/92% hero, no excess, prohibited steel excluded |
| Backhaul | Reverse opportunity found; short return window removes it |
| Cost/carbon | Charge sums equal totals; tonne-km math; urgent road recommendation |
| Scheduled capacity | Two loads share one service; third segment-overflow load rejected |
| State/booking | Full vertical slice through delivery; invalid jump, missing approval, duplicate booking |
| Recovery | Cancellation alternatives, approval required, replacement applied, road fallback under closure |
| Impact | Derived from persisted pool bookings; selected and completed tonnes separated; empty DB has zero impact |
| Security | Tenant/role checks, redacted captain records, non-demo header refusal, upload limits/signatures |
| Real browser | Text intake, Malayalam availability, hero constraints → pool → backhaul → booking → delivery → policy metrics, all 15 roles, mobile/offline map |

Screenshots are generated in `docs/screenshots`. Build output, browser traces/results and virtual environments are ignored by Git. A third-party Starlette/httpx deprecation notice may appear; it does not fail tests. CI runs backend tests and frontend compilation; browser tests are run locally against the app.

For reproducible computed evidence, run `.venv/Scripts/python.exe scripts/generate_measured_results.py` (`measure_demo.py` remains a compatibility wrapper). It uses isolated databases and generates `data/demo/measured-results.json`; no impact totals are hand-entered. Generate current-dated upload fixtures with `.venv/Scripts/python.exe scripts/make_demo_documents.py`.

## Continuation acceptance coverage

| Workflow / boundary | Evidence |
|---|---|
| Real scanned PDF OCR | `test_extension_boundaries.py` processes the committed scanned PDF through the actual local ONNX renderer/recognizer; no OCR mock in this test |
| OCR failure and document review | `test_intake_extensions.py` timeout/fallback, malformed image and nullable reviewed fields |
| XLSX import safety | Valid/invalid rows, formulas, duplicate mapped headers, large workbook rejection, scoped preview/error download, valid-only atomic import and reuse guard |
| Recurrence/contracts | Dated generation, per-segment overflow, occurrence cancellation, residual contract holds/rate draw and all-or-none rollback after the second reservation fails |
| Fleet optimization | Capacity/hard route rejection, prohibited co-loads, duplicate selection validation, objective/status and explicit atomic approval |
| Terminal resources | Berth/crane collision and alternate start, actual plan delay under equipment reservation, peak simultaneous quantity and union of all pooled members' equipment needs |
| Recovery | Four added failure variants plus originals, whole-pool combined capacity/feasibility and atomic member reassignment |
| Evidence/labels/POD | Type/size limits, private photo access, 128-bit opaque QR, unauthorized resolve, OTP hash/expiry/single-use/attempt limit and delivered gate |
| Admin/secondary scopes | Role assignment authorization, disable/revocation, own operator settlement visibility, captain financial redaction and crew/warehouse field boundaries |
| Intelligence | Actual corridor journey/deduplicated voyage statistics, small rate samples, report review/promotion, modal classification and typed failed-demand aggregation |
| Providers | Mocked valid/malformed/outage/transient-retry LLM/STT, varied Malayalam/mixed phrases, uncertain destinations, stale GPS and wrong-location weather fallback |
| Visible browser workflows | All original nine plus XLSX, recurrence/fleet approval, terminal conflict, photo/QR/OTP, admin/provider fallback and guided whole-pool recovery/impact |

The browser suite resets the running demo before each test, and captures real screenshots. An initial evidence browser assertion used the wrong heading; it was corrected and the final full suite passes. The actual scanned-PDF smoke check caught a renderer context-manager incompatibility; explicit page closure fixed it and the real-renderer acceptance test prevents regression.

## Final quality-gate evidence

Flagship intake → feasibility rejection → modes → 138 t pool → 62 t return opportunity → actual booking → states → government impact is covered in the original browser flow and guided optional-recovery flow. Reproducible measured cases separately confirm a four-hour road-wins scenario, terminal-only direct water, actual booked return impact, recovery cost/ETA change, generated recurrence and fleet assignment. Backend acceptance tests execute recurring bookings, terminal collisions and fleet approvals through actual services. Offline map/cache and provider failure tests pass. A fresh reset reports zero booking-derived impact.

Production build, formatting checks, local Markdown links, screenshot validity, ignored runtime artifacts, Git whitespace/status and basic redacted secret-signature scan are publication checks. Run `.venv/Scripts/python.exe scripts/check_repository.py`; the review covers README/docs local links and tracked/unignored files. npm production audit reported zero vulnerabilities. These checks do not certify navigation, external provider accuracy, production throughput, PostgreSQL concurrency or all possible secrets. External LLM/STT smoke probes explicitly skip because credentials are unconfigured.

Bounds: pool solver 2 s; fleet solver total 3 s / 40 cargo / 12 vessels; LLM HTTP 8 s per attempt and broker budget 16 s; text PDF worker 12 s / 40 pages; OCR worker 20 s / first four pages / bounded pixels; uploads 8 MB (evidence 2 MB); XLSX 200 rows / 40 columns / 32 MB decompressed; recurring generation 90 days / 12 reservations per approval; resource alternate-slot search 100 iterations. Tests prove selected bounds and rollback behavior, not production stress capacity.
