# Testing

Backend tests use a fresh seeded, foreign-key-enabled in-memory SQLite database for every test. They do not mutate the running demo. FastAPI integration tests go through actual schemas, RBAC, services and persistence.

Latest verified local results: **41 backend tests passed**, **9 Chromium end-to-end tests passed**, and the TypeScript/Vite production build passed. Browser coverage includes PDF upload, broker tool execution, explicitly approved recovery, scheduled capacity and captain cache reconnection guards. A real two-thread SQLite test verifies that simultaneous booking attempts produce one reservation and one conflict.

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

For reproducible computed evidence, run `.venv/Scripts/python.exe scripts/measure_demo.py`. It uses an isolated database and generates `data/demo/measured-results.json`; no impressive impact totals are hand-entered.
