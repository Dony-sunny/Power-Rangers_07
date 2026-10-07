# Feature audit

Reviewed against both user-supplied specifications on 7 October 2026. **Everything in the broad master prompt is not production-complete.** P0/P1 and the highest-value continuation workflows are implemented; the exact partial/roadmap boundaries are below. IMPLEMENTED means working in the documented synthetic prototype scope, not certified real-world deployment.

Statuses: IMPLEMENTED = an executable prototype workflow or satisfied artifact requirement; PARTIAL = working subset/interface with a stated gap; ROADMAP = no connected workflow; NOT APPLICABLE = context/historical/optional instruction rather than a current software feature. Missing/broken baseline gaps are resolved or represented by these final statuses, without silently calling architecture a completed integration.

## Baseline and verification

Before edits: clean commit `179470f`, 41 backend tests, 9 browser tests and production build passed. The first sandboxed esbuild invocation could not spawn; the authorized retry passed. The original architecture and vertical slice were preserved. Final results are recorded in [Testing](TESTING.md). No external AI/STT credentials or production connectors were tested. Existing origin points to Dony-sunny/keralAI_hack; this continuation made no push or repository creation, and remote visibility/content was not verified.

## All 56 master sections

| Section | Status | Source | Scope / remaining boundary |
|---|---|---|---|
| 1. HACKATHON CONTEXT AND DESIGN PRIORITIES | PARTIAL | [README.md](../README.md) | Five challenge flows work; these continuation commits were not pushed or hosted. Existing remote visibility/content is unverified. Organizer context is user-supplied, not a verified scoring rubric. |
| 2. FUNDAMENTAL PRODUCT PRINCIPLE | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py) | One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| 3. TECHNOLOGY STACK | IMPLEMENTED | [requirements.txt](../requirements.txt) | React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| 4. REPOSITORY STRUCTURE | IMPLEMENTED | [README.md](../README.md) | Requested module separation exists. Optional docker-compose is not necessary for the local artifact. |
| 5. ROLE-BASED WORKSPACES | PARTIAL | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx) | Fifteen distinct roles. Every listed role feature is individually assessed below. |
| 6. MULTI-TENANCY AND RBAC | IMPLEMENTED | [backend/auth.py](../backend/auth.py) | Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching. |
| 7. DOMAIN ENTITIES / DATABASE | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py) | Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| 8. KERALA / NW-3 DEMO DATA | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py) | Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| 9. MULTIMODAL SHIPPER INTAKE | IMPLEMENTED | [backend/api/intake.py](../backend/api/intake.py) | Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation. |
| 10. MALAYALAM VOICE VESSEL INTAKE | PARTIAL | [intelligence/voice_intake/parser.py](../intelligence/voice_intake/parser.py) | Recording/upload, STT adapter, native/transliterated/mixed variants, uncertainty and explicit fallback work. Real Malayalam provider accuracy/credentials remain untested. |
| 11. AGENTIC BROKER | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py) | Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| 12. HARD FEASIBILITY ENGINE | IMPLEMENTED | [feasibility/engine.py](../feasibility/engine.py) | Weight, volume, draft, air draft, beam, category/co-load, terminals/resources, windows/locks, maintenance and certificates with reasons. |
| 13. SMART MATCHING | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py) | Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| 14. LOAD POOLING | IMPLEMENTED | [optimization/pooling/solver.py](../optimization/pooling/solver.py) | CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation. |
| 15. BACKHAUL / EMPTY RETURN OPTIMIZER | IMPLEMENTED | [optimization/backhaul/search.py](../optimization/backhaul/search.py) | Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel. |
| 16. TERMINAL SELECTION OPTIMIZER | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py) | Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| 17. ROAD vs WATER vs HYBRID PLANNER | IMPLEMENTED | [backend/services/planning.py](../backend/services/planning.py) | Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup. |
| 18. CARBON CALCULATOR | IMPLEMENTED | [optimization/multimodal/costs.py](../optimization/multimodal/costs.py) | Configurable tonne-km factors with synthetic provenance; no certified emissions claim. |
| 19. SCHEDULED CARGO SERVICE PLANNER | IMPLEMENTED | [backend/services/recurring.py](../backend/services/recurring.py) | Dated patterns/stops/weekdays/capacities, recurring approval, per-segment reservations, one-occurrence cancellation and demand proposals with insufficient-history labels. |
| 20. QUOTE MARKETPLACE / RISK-ADJUSTED PROCUREMENT | PARTIAL | [backend/services/analytics.py](../backend/services/analytics.py) | Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial. |
| 21. CORRIDOR RELIABILITY | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py) | Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages. |
| 22. BOOKING RISK SCORE | PARTIAL | [backend/services/bookings.py](../backend/services/bookings.py) | Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor. |
| 23. BOOKING + SHIPMENT STATE MACHINE | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py) | Real request/booking/shipment state transitions, atomic reservations and forbidden skips. Failure/cancellation/replanning are persisted. |
| 24. EXCEPTION RECOVERY | PARTIAL | [backend/services/recovery.py](../backend/services/recovery.py) | Eight pre-departure disruptions, later schedule/replacement/terminal/service/road alternatives, deltas, approval and atomic whole-pool recovery. Split loads and mid-voyage rescue remain roadmap. |
| 25. WATERWAY CROWD REPORTING | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py) | Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| 26. FLOOD / RESILIENCE MODE | PARTIAL | [backend/api/demo.py](../backend/api/demo.py) | Deterministic road restriction, critical priority and labeled authority impact. Full emergency dispatch allocation and live flood observations are not connected. |
| 27. MODAL-SHIFT OPPORTUNITY ENGINE | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py) | Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| 28. FAILED-MATCH INTELLIGENCE | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py) | Search events and seven failure classes, corridor tonnage/frequency and unique request counts. |
| 29. TERMINAL ACTIVATION INTELLIGENCE | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py) | Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic. |
| 30. GOVERNMENT / IMPACT METRICS | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py) | Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| 31. TRACKING | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py) | Milestone positions/progress/timeline and ETA; simulated tracking is disclosed. Optional validated external read adapter exists. |
| 32. DOCUMENT GENERATION | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py) | All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |
| 33. TRUST / OPERATOR RELIABILITY | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx) | Profile/certificate validity and synthetic completed/on-time/cancellation/claim/reliability fields are visible, never represented as official verification. |
| 34. DEMO MODE | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py) | Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| 35. HERO DEMO DATA | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py) | 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| 36. UI / UX | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx) | Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| 37. SHIPPER HERO SCREEN | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx) | Cargo/route/deadline, road/water/hybrid cards, recommendation, cost/SLA/carbon/source explanation. |
| 38. OPERATOR HERO SCREEN | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx) | Capacity, demand, utilization/pool projection, return opportunity and potential revenue with disclosed deterministic or configured-AI provenance. |
| 39. GOVERNMENT HERO SCREEN | IMPLEMENTED | [frontend/src/components/Government.tsx](../frontend/src/components/Government.tsx) | Map/heatmap, selected/completed impact, utilization/backhaul/unserved and corridor/terminal gaps. |
| 40. SECURITY / PRIVACY | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md) | Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| 41. TESTING | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md) | Original and expanded meaningful unit/integration/browser checks; actual scanned-PDF OCR and transaction rollback covered. |
| 42. OBSERVABILITY | IMPLEMENTED | [backend/repositories/common.py](../backend/repositories/common.py) | Structured event audits/logging; no credentials or uploaded bodies logged. |
| 43. DEVELOPMENT ORDER | NOT APPLICABLE | [docs/CONTINUATION_PLAN.md](../docs/CONTINUATION_PLAN.md) | Historical build order: continuation first audited and verified the existing baseline, then preserved P0/P1 while extending it. |
| 44. P0 / P1 / P2 PRIORITIES | PARTIAL | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md) | P0/P1 and substantial P2 work; production WhatsApp/payment/insurance/government/IoT/predictive maintenance intentionally remain P3. |
| 45. NO FAKE AI RULE | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md) | Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| 46. PROVENANCE / EXPLAINABILITY | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md) | Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| 47. GITHUB QUALITY | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md) | Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| 48. REQUIRED DOCUMENTATION FILES | IMPLEMENTED | [README.md](../README.md) | All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| 49. HACKATHON_SUBMISSION.md | IMPLEMENTED | [docs/HACKATHON_SUBMISSION.md](../docs/HACKATHON_SUBMISSION.md) | Title, concise description, problem, solution, innovations, actual AI boundary, stack, readiness, demo, metrics and limitations. |
| 50. PROJECT PRESENTATION OUTLINE | IMPLEMENTED | [docs/PRESENTATION_OUTLINE.md](../docs/PRESENTATION_OUTLINE.md) | Requested nine-slide outline; an actual slide deck was not requested in place of the outline. |
| 51. THREE-MINUTE DEMO SCRIPT | IMPLEMENTED | [docs/DEMO_SCRIPT.md](../docs/DEMO_SCRIPT.md) | Three-minute manual story, optional guided checkpoints and failure fallback rehearsal. |
| 52. JUDGE-FACING EXPLANATIONS | IMPLEMENTED | [frontend/src/components/JudgeDemo.tsx](../frontend/src/components/JudgeDemo.tsx) | Judge-facing WHY for failure, modes, pooling, benchmarks, fleet assignment and recovery with computed deltas. |
| 53. PERFORMANCE / DEMO RELIABILITY | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md) | Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| 54. DEFINITION OF DONE | IMPLEMENTED | [tests/integration/test_vertical_slice.py](../tests/integration/test_vertical_slice.py) | The sixteen required vertical-slice outcomes are tested using actual domain services and persisted records. |
| 55. YOUR WORKING BEHAVIOR | IMPLEMENTED | [docs/CONTINUATION_PLAN.md](../docs/CONTINUATION_PLAN.md) | Action-oriented continuation, honest assumptions, bounded dependencies and documentation; no disconnected rebuild. |
| 56. FIRST ACTION | NOT APPLICABLE | [docs/CONTINUATION_PLAN.md](../docs/CONTINUATION_PLAN.md) | Original first-action instructions were superseded by the continuation audit/baseline/preserve instructions, which were followed. |

### Master 1: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| Maritime & Shipping | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| Logistics & Transportation | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| Supply Chain & Operations | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| Cargo owners | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| Boat operators | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| Logistics companies | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| Inland waterway service providers | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| increase utilization of Kerala waterways | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| enable sustainable logistics | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| clear project title | IMPLEMENTED | [docs/HACKATHON_SUBMISSION.md](../docs/HACKATHON_SUBMISSION.md). Requested local artifact/content exists; presentation scope is the supplied nine-slide outline. |
| concise project description | IMPLEMENTED | [docs/HACKATHON_SUBMISSION.md](../docs/HACKATHON_SUBMISSION.md). Requested local artifact/content exists; presentation scope is the supplied nine-slide outline. |
| problem → ideation → artifact progression | IMPLEMENTED | [docs/HACKATHON_SUBMISSION.md](../docs/HACKATHON_SUBMISSION.md). Requested local artifact/content exists; presentation scope is the supplied nine-slide outline. |
| GitHub repository | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local changes and publication commands prepared; this continuation performed no repository creation or remote push. |
| working software artifact | IMPLEMENTED | [docs/HACKATHON_SUBMISSION.md](../docs/HACKATHON_SUBMISSION.md). Requested local artifact/content exists; presentation scope is the supplied nine-slide outline. |
| project presentation | IMPLEMENTED | [docs/HACKATHON_SUBMISSION.md](../docs/HACKATHON_SUBMISSION.md). Requested local artifact/content exists; presentation scope is the supplied nine-slide outline. |
| project documentation | IMPLEMENTED | [docs/HACKATHON_SUBMISSION.md](../docs/HACKATHON_SUBMISSION.md). Requested local artifact/content exists; presentation scope is the supplied nine-slide outline. |
| clean submission readiness | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local changes and publication commands prepared; this continuation performed no repository creation or remote push. |
| 20% working end-to-end prototype | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| 20% AI/technical depth | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| 15% direct challenge alignment | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| 15% innovation/differentiation | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| 10% real-world feasibility | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| 10% measurable impact | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| 5% demo/presentation quality | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |
| 5% scalability/business viability | NOT APPLICABLE | [README.md](../README.md). Context or process requirement; implementation/artifact scope is assessed in the section matrix. |

### Master 2: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| vessel capacity | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| water depth | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| bridge clearance | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| vessel draft | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| terminal handling limits | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| hazardous cargo compatibility | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| cargo weight constraints | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| legal/compliance validity | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| optimization math | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |
| financial totals | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate. |

### Master 3: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| React | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| TypeScript | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Vite | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| responsive UI | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Leaflet + OpenStreetMap for maps | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Recharts or equivalent for charts | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| no unnecessary heavy UI framework unless justified | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Python | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| FastAPI | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Pydantic | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| SQLAlchemy | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| SQLite for hackathon/demo | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| database abstraction must allow later PostgreSQL migration | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Google OR-Tools | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| graph-based route model | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Dijkstra or A* for waterway routing where appropriate | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| an LLM provider when an API key is configured | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| deterministic/local demo fallback when API is unavailable | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| support audio upload/recording | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| design for Malayalam speech | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| local or configurable speech-to-text provider | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| if live transcription dependencies are unavailable, implement a deterministic demo transcript fallback so the live demo cannot fail | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| support PDF/document upload | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| extract text from text-based PDFs | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| support AI structured extraction | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| design multimodal/image-document support through provider abstraction | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| never silently invent missing fields | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| Git repository from the beginning | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| clean commit-ready structure | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| .gitignore | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| .env.example | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |
| reproducible setup | IMPLEMENTED | [requirements.txt](../requirements.txt). React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing. |

## Every master role feature

Each row preserves the supplied feature wording. Additional continuation implementations are assessed in the phase matrix below.

### A. SHIPPER PROCUREMENT / COMMERCIAL

| Feature | Status | Source / scope |
|---|---|---|
| create cargo manually | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| type cargo request in natural language | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| upload purchase order | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| upload invoice | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| upload BOQ | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| spreadsheet/bulk upload architecture | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| AI extraction into structured cargo data | PARTIAL | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Adapter and schema validation work; external credentials were not available. |
| review and confirm extracted fields | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| request quote | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| road vs water vs hybrid comparison | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| door-to-door total landed cost | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| ETA | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| delivery-window feasibility | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| carbon comparison | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| operator reliability | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| mode recommendation | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| preferred operators | PARTIAL | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Stored CargoPreference field only; no management/ranking preference UI. |
| historical rate view | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| approve booking | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| recurring capacity contract architecture | PARTIAL | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Capacity holds and agreed rates work; legal negotiation/invoicing is not connected. |
| shipment history | IMPLEMENTED | [frontend/src/components/Planner.tsx](../frontend/src/components/Planner.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### B. SHIPPER OPERATIONS / DISPATCH

| Feature | Status | Source / scope |
|---|---|---|
| shipment timeline | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| first-mile truck assignment | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| origin terminal | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal time slot | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| vessel assignment | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| cargo readiness | PARTIAL | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Warehouse records readiness; no physical sensor verification. |
| loading status | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| live/demo tracking | PARTIAL | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Demo tracking works; external provider adapter is separate from the map. |
| ETA | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| delay alerts | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| rescheduling | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| replacement vessel workflow | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| alternative terminal | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| road fallback | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| exception recovery | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| proof of handover | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### C. WAREHOUSE / LOADING SUPERVISOR

| Feature | Status | Source / scope |
|---|---|---|
| upcoming loads | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| packing status | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| actual weight | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| volume verification | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| cargo labels / QR architecture | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| loading sequence | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| loading equipment requirement | PARTIAL | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Terminal capability/resource checks enforce requirements; a dedicated warehouse equipment checklist is not exposed. |
| cargo compatibility | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| damage photos | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| gate-out | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| handover confirmation | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### D. CONSIGNEE / RECEIVER

| Feature | Status | Source / scope |
|---|---|---|
| incoming shipments | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| ETA | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| unloading window | PARTIAL | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). ETA/status and assigned tracking are visible; a dedicated planned unloading-window card is not exposed. |
| delivery status | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| proof of delivery | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| OTP/signature architecture | PARTIAL | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Secure local demo OTP works when requested; older milestone-only deliveries remain unverified. Receipt names are not legal signatures. |
| quantity discrepancy | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| damage report | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| photo evidence | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| delivery documentation | IMPLEMENTED | [frontend/src/components/Evidence.tsx](../frontend/src/components/Evidence.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### E. VESSEL OWNER / COMMERCIAL OPERATOR

| Feature | Status | Source / scope |
|---|---|---|
| vessel profile | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| vessel availability | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| available capacity | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| booking opportunities | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| AI cargo recommendations | PARTIAL | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Feasible recommendations work locally; real external model validation is pending. |
| current utilization | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| projected utilization | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| revenue | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| quote management | PARTIAL | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Automatic computed quotes/opportunities; no commercial negotiation editor. |
| backhaul opportunities | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| return-load opportunities | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| scheduled service participation | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| reliability metrics | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| payment/settlement visibility | IMPLEMENTED | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| demand heatmap | PARTIAL | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Network aggregate exists, but the operator view uses opportunity cards rather than a dedicated demand heatmap. |
| rate benchmark | PARTIAL | [frontend/src/components/Operator.tsx](../frontend/src/components/Operator.tsx). Shipper benchmark works; operator-specific benchmark UI is not yet exposed. |

### F. FLEET DISPATCHER

| Feature | Status | Source / scope |
|---|---|---|
| vessel fleet map | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Voyage tracking/network map exists; a dedicated all-vessel current-position map is not implemented. |
| vessel states: AVAILABLE LOADING SAILING UNLOADING MAINTENANCE | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| assign vessel | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Fleet previews assignments; dispatch/control/admin approve consequential bookings. |
| assign crew architecture | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| schedule optimizer | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| booking conflicts | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| empty-leg reduction | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| vessel repositioning | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). One-voyage optimizer includes graph reposition distance/readiness; no multi-tour relocation dispatch. |
| terminal synchronization | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| route alerts | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Restrictions and recovery are visible; no push notification feed. |
| replacement vessel | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Dispatch/control approval workflow; fleet can view but cannot override recovery authorization. |
| operational control board | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### G. CAPTAIN / VESSEL MASTER

| Feature | Status | Source / scope |
|---|---|---|
| current voyage | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| cargo manifest | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| approved route | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| route restrictions | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| departure time | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| ETA | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal instructions | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| bridge/lock/route constraints | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| weather field architecture | PARTIAL | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Validated adapter/read endpoint exists; captain weather card and authoritative safety rule remain extensions. |
| incident report | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| departure confirmation | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| arrival confirmation | IMPLEMENTED | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| position update | PARTIAL | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Milestone simulation and optional read adapter; manual GPS capture/live map ingestion not connected. |
| navigation notices | PARTIAL | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Configured restrictions and reviewed observations; official notice feed not connected. |
| offline-friendly design | PARTIAL | [frontend/src/components/Tracking.tsx](../frontend/src/components/Tracking.tsx). Cached labeled read view and local map; disconnected writes/synchronization remain roadmap. |

### H. TERMINAL / JETTY OPERATOR

| Feature | Status | Source / scope |
|---|---|---|
| berth/jetty calendar | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| vessel arrival queue | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| loading slots | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| unloading slots | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| equipment allocation | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| storage availability | PARTIAL | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Capacity enforced during handling reservations; long-term warehouse inventory occupancy is not modeled. |
| truck appointments | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| gate status | PARTIAL | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Appointment starts EXPECTED and warehouse gate-out can be recorded; full gate lifecycle editing/scanning is not implemented. |
| handling completion | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal delay | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal charges | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| operational status | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### I. LOGISTICS COMPANY / 3PL CONTROL TOWER

| Feature | Status | Source / scope |
|---|---|---|
| all active shipments | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| on-track | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Timeline/risk board provides status; dedicated per-SLA on-track counters remain partial. |
| at-risk | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| delayed | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Risk and recovery/delay records exist; automatic lateness monitoring is not running. |
| intervention-required | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| bulk shipment management | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| vessel allocation | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| carrier/operator scorecards | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Synthetic profile metrics and corridor analytics; no dedicated 3PL scorecard comparison. |
| cost analytics | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Per-booking cost and fleet/impact calculations; a dedicated cost trend dashboard is not implemented. |
| SLA analytics | PARTIAL | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Plan SLA and actual on-time corridor metrics; contract-specific SLA penalty reporting remains roadmap. |
| exception queue | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| multimodal planning | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| cargo pooling overview | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| network view | IMPLEMENTED | [frontend/src/components/Advanced.tsx](../frontend/src/components/Advanced.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### J. FINANCE / SETTLEMENT

| Feature | Status | Source / scope |
|---|---|---|
| quote | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| accepted rate | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| first-mile charges | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal charges | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| water freight | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| waiting charges | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| last-mile charges | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| invoice | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| payment status | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| operator payout | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| escrow architecture | PARTIAL | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Payment contract/prototype states only; no held funds or real escrow. |
| dispute record | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| settlement history | IMPLEMENTED | [frontend/src/components/Workspaces.tsx](../frontend/src/components/Workspaces.tsx). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### K. COMPLIANCE / SAFETY

| Feature | Status | Source / scope |
|---|---|---|
| vessel registration | IMPLEMENTED | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| insurance | IMPLEMENTED | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| document expiry | IMPLEMENTED | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| operator verification | PARTIAL | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Platform demo certificate/organization verification; no legal identity/authenticity integration. |
| cargo restrictions | IMPLEMENTED | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| dangerous-goods compatibility | IMPLEMENTED | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| pre-voyage checklist | PARTIAL | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Computed compliance/feasibility checks; a separate signed checklist document is not implemented. |
| compliance PASS/FAIL | IMPLEMENTED | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| audit trail | IMPLEMENTED | [feasibility/compliance/checks.py](../feasibility/compliance/checks.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### L. MAINTENANCE

| Feature | Status | Source / scope |
|---|---|---|
| vessel maintenance state | IMPLEMENTED | [backend/api/operations.py](../backend/api/operations.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| defect report | IMPLEMENTED | [backend/api/operations.py](../backend/api/operations.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| inspection | IMPLEMENTED | [backend/api/operations.py](../backend/api/operations.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| downtime | IMPLEMENTED | [backend/api/operations.py](../backend/api/operations.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| return-to-service | IMPLEMENTED | [backend/api/operations.py](../backend/api/operations.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| maintenance due date | IMPLEMENTED | [backend/api/operations.py](../backend/api/operations.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| bookable vessel must pass maintenance availability | IMPLEMENTED | [backend/api/operations.py](../backend/api/operations.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### M. WATERWAY / NETWORK CONTROL

| Feature | Status | Source / scope |
|---|---|---|
| waterway map | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| segments | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| operational restrictions | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| lock status architecture | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Configured lock hours and deterministic waits; no live gates/authority bookings. |
| depth records | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| obstruction reports | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal status | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| route closure | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| navigation alerts | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). UI restrictions/observations; no external notice ingestion or push alerts. |
| traffic | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Vessel states and queues are available; full waterway traffic monitoring/map layers are not implemented. |
| demand heatmap | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| infrastructure observations | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### N. GOVERNMENT / POLICY ANALYTICS

| Feature | Status | Source / scope |
|---|---|---|
| cargo shifted from road to water | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| estimated truck trips avoided | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| estimated CO2 avoided | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| vessel utilization before/after | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| backhaul matches | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| corridor demand | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| failed searches | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| unmatched cargo demand | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| capacity gaps | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal utilization | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| modal-shift opportunities | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| terminal activation intelligence | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| infrastructure priority insights | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### O. PLATFORM ADMIN / TRUST

| Feature | Status | Source / scope |
|---|---|---|
| organization/user management | IMPLEMENTED | [backend/api/admin.py](../backend/api/admin.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| role management | IMPLEMENTED | [backend/api/admin.py](../backend/api/admin.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| verification | PARTIAL | [backend/api/admin.py](../backend/api/admin.py). Prototype certificate/organization records; no production identity/document authenticity workflow. |
| audit logs | IMPLEMENTED | [backend/api/admin.py](../backend/api/admin.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| dispute administration | IMPLEMENTED | [backend/api/admin.py](../backend/api/admin.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| model/provider status | IMPLEMENTED | [backend/api/admin.py](../backend/api/admin.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |
| seed/demo data management | IMPLEMENTED | [backend/api/admin.py](../backend/api/admin.py). Working in the disclosed prototype scope; see workspace coverage for the exact user action. |

### Master 6: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| shipper | IMPLEMENTED | [backend/auth.py](../backend/auth.py). Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching. |
| operator | IMPLEMENTED | [backend/auth.py](../backend/auth.py). Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching. |
| logistics/3PL | IMPLEMENTED | [backend/auth.py](../backend/auth.py). Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching. |
| terminal operator | IMPLEMENTED | [backend/auth.py](../backend/auth.py). Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching. |
| authority | IMPLEMENTED | [backend/auth.py](../backend/auth.py). Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching. |
| government | IMPLEMENTED | [backend/auth.py](../backend/auth.py). Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching. |

### Master 7: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| Organization | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| User | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| Role | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| CargoRequest | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| CargoDocument | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| CargoPreference | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| Vessel | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| VesselAvailability | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| VesselCertificate | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| VesselMaintenanceStatus | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| WaterwayNode | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| WaterwaySegment | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| RouteRestriction | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| NavigationReport | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| Terminal | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| TerminalCapability | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| TerminalSlot | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| TransportQuote | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| MatchRecommendation | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| PoolingGroup | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| BackhaulOpportunity | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| ScheduledService | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| ScheduledServiceStop | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| ScheduledCapacityBooking | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| Booking | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| Shipment | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| ShipmentLeg | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| TrackingEvent | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| InvoiceRecord | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| PaymentRecord | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| ComplianceCheck | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| ImpactMetric | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| AuditEvent | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| id | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| cargo_type | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| weight_tonnes | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| volume_m3 | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| packaging | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| fragile | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| perishable | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| hazardous | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| temperature_control_required | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| origin | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| destination | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| origin coordinates if known | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| destination coordinates if known | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| ready_time | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| delivery_deadline | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| first_mile_required | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| last_mile_required | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| consolidation_allowed | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| prohibited_co_load_categories | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| budget | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| priority | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| id | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| name | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| operator | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| vessel_type | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| max_capacity_tonnes | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| max_volume_m3 | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| length | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| beam | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| loaded_draft | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| air_draft | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| current_location | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| cargo_categories | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| maintenance_status | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| compliance_status | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| reliability_score | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| source_node | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| destination_node | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| distance | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| available_depth | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| minimum_width | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| minimum_bridge_clearance | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| lock_required | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| lock_name | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| navigation_status | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| restriction | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| source_name | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| source_date | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| confidence | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| last_verified | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| terminal | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| cargo_types | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| jetty_length | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| available_storage | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| covered_storage | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| crane_available | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| crane_capacity | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| forklift_available | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| forklift_capacity | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| road_access | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| approach_channel | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |
| operational_status | IMPLEMENTED | [backend/models/domain.py](../backend/models/domain.py). Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows. |

### Master 8: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| NW-3 is approximately 205 km overall | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| it includes the West Coast Canal and major connecting canals | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| the system is tidally influenced | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| lock gates exist at Thanneermukkom and Thrikunnapuzha | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| route geometry/depth/clearance is not conceptually uniform | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| terminals including Maradu, Vaikom, Thanneermukkom and Alappuzha are useful demonstration points | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| source-grounded data | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| prototype assumptions | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| synthetic/demo values | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |
| live integrations not yet connected | IMPLEMENTED | [data/seed/network.py](../data/seed/network.py). Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope. |

### Master 9: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| natural-language text | IMPLEMENTED | [backend/api/intake.py](../backend/api/intake.py). Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation. |
| PDF | IMPLEMENTED | [backend/api/intake.py](../backend/api/intake.py). Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation. |
| invoice | IMPLEMENTED | [backend/api/intake.py](../backend/api/intake.py). Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation. |
| purchase order | IMPLEMENTED | [backend/api/intake.py](../backend/api/intake.py). Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation. |
| BOQ | IMPLEMENTED | [backend/api/intake.py](../backend/api/intake.py). Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation. |
| future spreadsheet support "cargo_type": "cement", "weight_tonnes": 80, "volume_m3": null, "packaging": "bagged", "origin": "Kalamassery", "destination": "Alappuzha", "delivery_deadline": "...", "fragile": false, "hazardous": false, "confidence": { ... }, "missing_fields": [...] | IMPLEMENTED | [backend/api/intake.py](../backend/api/intake.py). Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation. |

### Master 10: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| compatible cargo | PARTIAL | [intelligence/voice_intake/parser.py](../intelligence/voice_intake/parser.py). Recording/upload, STT adapter, native/transliterated/mixed variants, uncertainty and explicit fallback work. Real Malayalam provider accuracy/credentials remain untested. |
| potential pooled cargo | PARTIAL | [intelligence/voice_intake/parser.py](../intelligence/voice_intake/parser.py). Recording/upload, STT adapter, native/transliterated/mixed variants, uncertainty and explicit fallback work. Real Malayalam provider accuracy/credentials remain untested. |
| possible backhaul | PARTIAL | [intelligence/voice_intake/parser.py](../intelligence/voice_intake/parser.py). Recording/upload, STT adapter, native/transliterated/mixed variants, uncertainty and explicit fallback work. Real Malayalam provider accuracy/credentials remain untested. |
| projected utilization | PARTIAL | [intelligence/voice_intake/parser.py](../intelligence/voice_intake/parser.py). Recording/upload, STT adapter, native/transliterated/mixed variants, uncertainty and explicit fallback work. Real Malayalam provider accuracy/credentials remain untested. |
| potential revenue | PARTIAL | [intelligence/voice_intake/parser.py](../intelligence/voice_intake/parser.py). Recording/upload, STT adapter, native/transliterated/mixed variants, uncertainty and explicit fallback work. Real Malayalam provider accuracy/credentials remain untested. |

### Master 11: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| parse_cargo_document() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| parse_cargo_text() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| parse_vessel_voice() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| get_cargo() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| get_vessel() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| get_terminal() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| get_route_data() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| find_candidate_vessels() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| check_vessel_capacity() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| check_cargo_compatibility() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| check_waterway_feasibility() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| check_terminal_feasibility() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| check_compliance() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| rank_matches() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| optimize_load_pool() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| find_backhaul() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| choose_origin_terminal() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| choose_destination_terminal() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| compare_transport_modes() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| find_scheduled_services() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| propose_scheduled_service() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| request_quote() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| create_booking() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| generate_manifest() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| generate_transport_instruction() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| get_tracking_status() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| replan_shipment() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| calculate_impact() | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| determine which tool to call | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| interpret user requests | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| summarize results | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| explain recommendations | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |
| translate Malayalam/English | PARTIAL | [intelligence/broker_agent/agent.py](../intelligence/broker_agent/agent.py). Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated. |

### Master 13: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| capacity fit | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| route compatibility | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| schedule fit | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| total cost | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| operator reliability | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| utilization improvement | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| backhaul opportunity | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |
| carbon impact | IMPLEMENTED | [optimization/matching/engine.py](../optimization/matching/engine.py). Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview. |

### Master 14: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| maximize utilization | IMPLEMENTED | [optimization/pooling/solver.py](../optimization/pooling/solver.py). CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation. |
| maximize compatible revenue | IMPLEMENTED | [optimization/pooling/solver.py](../optimization/pooling/solver.py). CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation. |
| minimize route deviation | IMPLEMENTED | [optimization/pooling/solver.py](../optimization/pooling/solver.py). CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation. |
| minimize handling complexity | IMPLEMENTED | [optimization/pooling/solver.py](../optimization/pooling/solver.py). CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation. |
| satisfy deadlines | IMPLEMENTED | [optimization/pooling/solver.py](../optimization/pooling/solver.py). CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation. |
| obey co-load constraints | IMPLEMENTED | [optimization/pooling/solver.py](../optimization/pooling/solver.py). CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation. |

### Master 15: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| available departure window | IMPLEMENTED | [optimization/backhaul/search.py](../optimization/backhaul/search.py). Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel. |
| route | IMPLEMENTED | [optimization/backhaul/search.py](../optimization/backhaul/search.py). Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel. |
| cargo compatibility | IMPLEMENTED | [optimization/backhaul/search.py](../optimization/backhaul/search.py). Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel. |
| capacity | IMPLEMENTED | [optimization/backhaul/search.py](../optimization/backhaul/search.py). Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel. |
| revenue | IMPLEMENTED | [optimization/backhaul/search.py](../optimization/backhaul/search.py). Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel. |
| schedule | IMPLEMENTED | [optimization/backhaul/search.py](../optimization/backhaul/search.py). Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel. |

### Master 16: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| first-mile distance/cost | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| terminal capability | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| terminal waiting | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| handling cost | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| vessel feasibility | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| waterway distance | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| destination handling | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| last-mile distance/cost | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |
| deadline | IMPLEMENTED | [optimization/terminal_selection/planner.py](../optimization/terminal_selection/planner.py). Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation. |

### Master 17: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| total cost | IMPLEMENTED | [backend/services/planning.py](../backend/services/planning.py). Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup. |
| ETA | IMPLEMENTED | [backend/services/planning.py](../backend/services/planning.py). Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup. |
| number of handoffs | IMPLEMENTED | [backend/services/planning.py](../backend/services/planning.py). Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup. |
| SLA feasibility | IMPLEMENTED | [backend/services/planning.py](../backend/services/planning.py). Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup. |
| reliability/risk | IMPLEMENTED | [backend/services/planning.py](../backend/services/planning.py). Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup. |
| CO2 estimate | IMPLEMENTED | [backend/services/planning.py](../backend/services/planning.py). Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup. |

### Master 20: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| price | PARTIAL | [backend/services/analytics.py](../backend/services/analytics.py). Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial. |
| reliability | PARTIAL | [backend/services/analytics.py](../backend/services/analytics.py). Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial. |
| cancellation rate | PARTIAL | [backend/services/analytics.py](../backend/services/analytics.py). Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial. |
| feasibility | PARTIAL | [backend/services/analytics.py](../backend/services/analytics.py). Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial. |
| ETA | PARTIAL | [backend/services/analytics.py](../backend/services/analytics.py). Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial. |
| total value/risk | PARTIAL | [backend/services/analytics.py](../backend/services/analytics.py). Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial. |

### Master 21: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| average/median journey duration | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages. |
| terminal wait | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages. |
| successful deliveries | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages. |
| cancellation | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages. |
| incident count | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages. |
| on-time rate | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages. |

### Master 22: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| operator reliability | PARTIAL | [backend/services/bookings.py](../backend/services/bookings.py). Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor. |
| schedule slack | PARTIAL | [backend/services/bookings.py](../backend/services/bookings.py). Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor. |
| terminal status | PARTIAL | [backend/services/bookings.py](../backend/services/bookings.py). Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor. |
| route restrictions | PARTIAL | [backend/services/bookings.py](../backend/services/bookings.py). Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor. |
| weather placeholder/provider | PARTIAL | [backend/services/bookings.py](../backend/services/bookings.py). Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor. |
| cargo complexity | PARTIAL | [backend/services/bookings.py](../backend/services/bookings.py). Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor. |

### Master 25: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| aquatic vegetation | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| shallow section | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| fishing obstruction | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| debris | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| terminal delay | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| navigation hazard | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| location | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| type | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| time | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| reporter | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| confidence | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| verification status | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |
| expiry | PARTIAL | [backend/api/analytics.py](../backend/api/analytics.py). Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented. |

### Master 26: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| specified road corridor can become unavailable/high risk | PARTIAL | [backend/api/demo.py](../backend/api/demo.py). Deterministic road restriction, critical priority and labeled authority impact. Full emergency dispatch allocation and live flood observations are not connected. |
| critical cargo can receive priority | PARTIAL | [backend/api/demo.py](../backend/api/demo.py). Deterministic road restriction, critical priority and labeled authority impact. Full emergency dispatch allocation and live flood observations are not connected. |
| system attempts available water/hybrid plans | PARTIAL | [backend/api/demo.py](../backend/api/demo.py). Deterministic road restriction, critical priority and labeled authority impact. Full emergency dispatch allocation and live flood observations are not connected. |
| authority dashboard shows emergency allocation | PARTIAL | [backend/api/demo.py](../backend/api/demo.py). Deterministic road restriction, critical priority and labeled authority impact. Full emergency dispatch allocation and live flood observations are not connected. |

### Master 27: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| tonnage | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| urgency | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| cargo type | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| origin proximity | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| destination proximity | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| handling requirements | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| waterway availability | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |
| frequency | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction. |

### Master 29: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| nearby cargo demand | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic. |
| available vessel supply | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic. |
| handling capability | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic. |
| road connectivity data/placeholder | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic. |
| current platform utilization | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic. |
| failed-match demand | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic. |

### Master 30: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| road baseline cost | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| chosen plan cost | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| road baseline emissions estimate | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| chosen plan emissions estimate | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| baseline truck movements | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| vessel utilization before | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| vessel utilization after | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| empty return avoided | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |
| tonnes shifted to water | IMPLEMENTED | [backend/services/impact.py](../backend/services/impact.py). Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps. |

### Master 31: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| vessel position | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). Milestone positions/progress/timeline and ETA; simulated tracking is disclosed. Optional validated external read adapter exists. |
| shipment progress | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). Milestone positions/progress/timeline and ETA; simulated tracking is disclosed. Optional validated external read adapter exists. |
| milestone tracking | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). Milestone positions/progress/timeline and ETA; simulated tracking is disclosed. Optional validated external read adapter exists. |
| ETA | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). Milestone positions/progress/timeline and ETA; simulated tracking is disclosed. Optional validated external read adapter exists. |
| status timeline | IMPLEMENTED | [backend/services/bookings.py](../backend/services/bookings.py). Milestone positions/progress/timeline and ETA; simulated tracking is disclosed. Optional validated external read adapter exists. |

### Master 32: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| booking confirmation | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py). All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |
| cargo manifest | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py). All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |
| loading sheet | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py). All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |
| transport instruction | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py). All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |
| delivery note | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py). All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |
| invoice draft | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py). All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |
| proof-of-delivery record | IMPLEMENTED | [backend/services/documents.py](../backend/services/documents.py). All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts. |

### Master 34: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| cargo | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| vessels | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| routes | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| terminals | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| restrictions | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| quotes | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| scheduled services | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |
| tracking events | IMPLEMENTED | [backend/api/demo.py](../backend/api/demo.py). Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services. |

### Master 35: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| voice extraction | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| document/text extraction | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| multiple vessel candidates | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| one attractive candidate failing hard feasibility | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| another candidate passing | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| road/water/hybrid comparison | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| load pooling raising utilization to approximately 90%+ | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| return cargo opportunity | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| booking | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| tracking | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |
| impact calculation | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). 80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures. |

### Master 36: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| clean enterprise layout | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| readable typography | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| responsive design | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| map-heavy operational screens | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| clear state/status indicators | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| meaningful empty states | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| loading/error handling | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| accessible forms | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| mobile-first captain/operator voice experience | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| excessive animations | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| fake AI gradients everywhere | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| unnecessary landing-page sections | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| giant marketing pages before the actual application | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |
| login screens consuming demo time | IMPLEMENTED | [frontend/src/App.tsx](../frontend/src/App.tsx). Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher. |

### Master 40: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| environment variables | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| no hard-coded secrets | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| input validation | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| upload size/type restrictions | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| sanitized filenames | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| safe document processing | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| backend authorization architecture | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| audit events | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| basic CORS configuration | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| no arbitrary file execution | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |
| error messages without secret leakage | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps. |

### Master 44: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| cargo creation | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| vessel availability | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| document/text intake | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| Malayalam voice demo intake | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| route feasibility | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| terminal feasibility | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| smart matching | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| road/water/hybrid comparison | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| booking | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| shipment state | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| load pooling | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| backhaul | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| terminal optimization | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| scheduled cargo services | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| tracking | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| impact calculator | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| government demand heatmap | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| control tower | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| exception recovery | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| failed-match intelligence | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| corridor reliability | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| booking risk | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| rate benchmarking | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| modal-shift advisor | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| flood mode | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| crowd navigation reporting | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| terminal activation scoring | IMPLEMENTED | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). Working prototype; individual limits are documented in the section matrix. |
| full WhatsApp Business integration | ROADMAP | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). P0/P1 and substantial P2 work; production WhatsApp/payment/insurance/government/IoT/predictive maintenance intentionally remain P3. |
| production payment integration | PARTIAL | [backend/services/connectors.py](../backend/services/connectors.py). Typed no-op/provider contract only. Prototype / Not connected. |
| insurance provider integration | PARTIAL | [backend/services/connectors.py](../backend/services/connectors.py). Typed no-op/provider contract only. Prototype / Not connected. |
| advanced predictive maintenance | ROADMAP | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). P0/P1 and substantial P2 work; production WhatsApp/payment/insurance/government/IoT/predictive maintenance intentionally remain P3. |
| cold-chain IoT | ROADMAP | [docs/FUTURE_ROADMAP.md](../docs/FUTURE_ROADMAP.md). P0/P1 and substantial P2 work; production WhatsApp/payment/insurance/government/IoT/predictive maintenance intentionally remain P3. |
| external government workflow integrations | PARTIAL | [backend/services/connectors.py](../backend/services/connectors.py). Typed no-op/provider contract only. Prototype / Not connected. |

### Master 45: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| multimodal document understanding | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| multilingual natural-language understanding | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| Malayalam voice understanding | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| agent/tool orchestration | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| optional explanation generation | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| OR-Tools cargo pooling | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| backhaul search | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| terminal selection | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |
| scheduled capacity planning | IMPLEMENTED | [docs/AI_AND_OPTIMIZATION.md](../docs/AI_AND_OPTIMIZATION.md). Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations. |

### Master 46: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| capacity fit 98% | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| route feasible | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| schedule fit 94% | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| projected utilization 91% | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| reliability 96% | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| lower delivered cost | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| source type | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| data freshness where applicable | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |
| demo/simulated label when applicable | IMPLEMENTED | [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings. |

### Master 47: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| meaningful folder structure | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| no secrets | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| no junk files | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| no final2.py / testfinal.py style filenames | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| README | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| setup instructions | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| architecture | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| API documentation | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| screenshots if possible | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| demo instructions | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| assumptions | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| data provenance | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| tests | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| known limitations | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |
| roadmap | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed. |

### Master 48: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| system architecture | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| role architecture | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| data flow | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| agent/tool architecture | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| what uses LLM | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| what uses deterministic constraints | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| what uses OR-Tools | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| why this separation prevents hallucination | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| real/source-grounded | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| simulated | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| assumptions | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |
| external integrations | IMPLEMENTED | [README.md](../README.md). All required docs exist and are updated, plus coverage/provider/migration/publication guides. |

### Master 53: listed requirements

| Feature / requirement | Status | Source / scope |
|---|---|---|
| one-command or two-command startup | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| clear setup instructions | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| seed database command | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| demo reset command | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| no dependency on external API for the main deterministic workflow | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| graceful LLM/provider failure | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| graceful map/network failure where possible | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| obvious error messages | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| no long blocking operations in UI | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |
| pre-load demo fixtures | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified. |

## Continuation phase coverage

| Phase | Status | Source / result |
|---|---|---|
| 0 | IMPLEMENTED | [docs/CONTINUATION_PLAN.md](../docs/CONTINUATION_PLAN.md). Code audit, baseline before edits and prioritized preservation plan. |
| 1 | PARTIAL | [intelligence/provider/llm.py](../intelligence/provider/llm.py). Three clean provider classes, diagnostics, timeout/malformed/retry mocks and fallback; real credentials unavailable. |
| 2 | PARTIAL | [intelligence/voice_intake/parser.py](../intelligence/voice_intake/parser.py). Mic/upload/STT path and varied Malayalam/mixed phrases with confirmation; real provider speech evaluation pending. |
| 3 | IMPLEMENTED | [intelligence/document_intake/ocr_worker.py](../intelligence/document_intake/ocr_worker.py). Actual local scanned PDF/PNG/JPEG OCR, text first, bounded workers, metadata fields/review. Malayalam OCR is not validated; invoices/BOQ use generic extraction. |
| 4 | IMPLEMENTED | [intelligence/document_intake/spreadsheets.py](../intelligence/document_intake/spreadsheets.py). XLSX/template, deterministic aliases, per-row errors/warnings, formula/duplicate-header limits, valid-only atomic import and error download. |
| 5 | IMPLEMENTED | [backend/services/evidence.py](../backend/services/evidence.py). Private safe image evidence, uploader/timestamp/category, role workspaces and admin dispute view. Prototype DB storage, not production object storage. |
| 6 | IMPLEMENTED | [backend/services/evidence.py](../backend/services/evidence.py). 128-bit opaque cargo/booking/shipment QR references, printable labels and authorized hash navigation; no public commercial payload. |
| 7 | PARTIAL | [backend/services/evidence.py](../backend/services/evidence.py). Salted expiring single-use local OTP with receiver identity, five attempts and issuance limits. Requesting a challenge enforces verification; legacy demo milestone delivery remains explicitly unverified. No legal signature or SMS. |
| 8 | IMPLEMENTED | [backend/services/recurring.py](../backend/services/recurring.py). Dated patterns, segment occupancy, recurring booking, cancellation and suggested-service evidence labels. |
| 9 | IMPLEMENTED | [optimization/fleet.py](../optimization/fleet.py). Bounded multi-vessel/cargo CP-SAT, five objective profiles, hard combined validation and atomic approval. One voyage per vessel, not full multi-tour VRP. |
| 10 | IMPLEMENTED | [backend/services/terminal_resources.py](../backend/services/terminal_resources.py). Berth/equipment/storage/gate capacity checks, queue/alternate slots, appointments and handling/delay records; fixed handling duration and prototype storage intervals. |
| 11 | PARTIAL | [backend/services/recovery.py](../backend/services/recovery.py). Eight disruption types, affected-only replanning, replacement/later/service/terminal/road alternatives, deltas and whole-pool approval. No split-load or mid-voyage recovery. |
| 12 | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Corridor actual milestone aggregates, voyage deduplication, insufficient-sample score and disruption/cancellation counts. |
| 13 | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Comparable corridor/class/weight/time rates, source/sample size and minimum three observations; synthetic history is labeled, not industry rates. |
| 14 | IMPLEMENTED | [backend/api/analytics.py](../backend/api/analytics.py). Confidence/expiry, photos and VERIFIED/DISPUTED review with explicit restriction promotion; observation review is not official authority verification. |
| 15 | IMPLEMENTED | [backend/services/recurring.py](../backend/services/recurring.py). Commercial fields, reserved service capacity, contract draws and applied agreed water rate; legal negotiation/settlement penalties are not implied. |
| 16 | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Historical road CSV/XLSX suitability and potential aggregates; replay uses current demo availability, not reconstruction of historical safety. |
| 17 | IMPLEMENTED | [backend/services/analytics.py](../backend/services/analytics.py). Seven failure reasons, unique tonnage/frequency and price rejection. |
| 18 | IMPLEMENTED | [backend/api/admin.py](../backend/api/admin.py). Organization/user creation, role assignment/change, disable, membership and audits; stored signed identities retained. |
| 19 | PARTIAL | [docs/WORKSPACE_COVERAGE.md](../docs/WORKSPACE_COVERAGE.md). Fifteen roles audited; reused data for crew, gate/loading, handling, appointments, evidence, payment/disputes and admin. Remaining secondary gaps explicitly listed above. |
| 20 | IMPLEMENTED | [backend/services/connectors.py](../backend/services/connectors.py). Demo/external validated tracking interface with freshness/fallback; optional read endpoint, no live AIS claim. |
| 21 | IMPLEMENTED | [backend/services/connectors.py](../backend/services/connectors.py). Demo/external weather interface, schema/freshness/location fallback; no automatic hard-safety override or IMD claim. |
| 22 | IMPLEMENTED | [backend/services/connectors.py](../backend/services/connectors.py). Requested interface-only payment/insurance/government contracts, demo/no-op defaults, visible Not connected states. |
| 23 | IMPLEMENTED | [docs/POSTGRESQL_MIGRATION.md](../docs/POSTGRESQL_MIGRATION.md). Model review, driver/URL/migration/concurrency/deployment plan; SQLite retained. PostgreSQL deployment/Alembic rehearsal is still roadmap. |
| 24 | IMPLEMENTED | [docs/SECURITY.md](../docs/SECURITY.md). Signed identity maintained, future verification interface and OIDC/OAuth2/SSO mapping documented; no heavy identity service introduced. |
| 25 | PARTIAL | [docs/GITHUB_PUBLICATION.md](../docs/GITHUB_PUBLICATION.md). Secrets/links/screenshots/checks/readiness and exact commands; no public creation or push without approval. |
| 26 | IMPLEMENTED | [scripts/generate_measured_results.py](../scripts/generate_measured_results.py). Actual services in isolated databases generate all requested metrics and separate direct-water/road-wins/return/recovery/recurrence/fleet cases. |
| 27 | IMPLEMENTED | [frontend/src/components/JudgeDemo.tsx](../frontend/src/components/JudgeDemo.tsx). Demo-only clean checkpoints, approvals, reset and computed evidence; actual app services. |
| 28 | IMPLEMENTED | [backend/api/judge.py](../backend/api/judge.py). Guided flagship from confirmed intake to pool/booking/optional whole-pool recovery/departure/impact, with manual screens preserved. |
| 29 | IMPLEMENTED | [frontend/src/components/JudgeDemo.tsx](../frontend/src/components/JudgeDemo.tsx). Readable failure, score, price, utilization, benchmark, fleet and recovery explanations with synthetic-source labels. |
| 30 | IMPLEMENTED | [docs/FEATURE_AUDIT.md](../docs/FEATURE_AUDIT.md). All requested docs updated; this catalog covers all master sections, role features, listed requirements and continuation phases. |
| 31 | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Acceptance tests for new boundaries plus all original tests; actual PDF renderer, capacity/compatibility, authorization and rollback tested. |
| 32 | IMPLEMENTED | [docs/KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md). Workload/timeout bounds, best feasible solver status, loading/errors and atomic writes; production stress certification remains out of scope. |
| 33 | IMPLEMENTED | [docs/TESTING.md](../docs/TESTING.md). Final local gate is recorded after running original/extended tests, build, measured cases, offline/failure checks, reset, links and security review. |

The catalog is a checked-in extraction of the supplied master feature lists, not a claim that test counts prove every production integration. Re-render with `python scripts/update_feature_audit.py`. Remaining production requirements are expanded in [Known limitations](KNOWN_LIMITATIONS.md), [Roadmap](FUTURE_ROADMAP.md), [Provider setup](PROVIDER_SETUP.md) and [Publication](GITHUB_PUBLICATION.md).
