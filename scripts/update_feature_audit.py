"""Render the reviewed specification catalog as source-linked feature coverage."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Status describes the requested prototype scope, not production certification.
SECTION = {
    1: (
        "PARTIAL",
        "README.md",
        "Five challenge flows work; these continuation commits were not pushed or hosted. Existing remote visibility/content is unverified. Organizer context is user-supplied, not a verified scoring rubric.",
    ),
    2: (
        "IMPLEMENTED",
        "backend/services/bookings.py",
        "One shared freight twin; interpretation, hard constraints, optimization and transaction truth remain separate.",
    ),
    3: (
        "IMPLEMENTED",
        "backend/requirements.txt",
        "React/TS/Vite, Leaflet, Recharts, FastAPI/Pydantic/SQLAlchemy/SQLite, OR-Tools and graph routing.",
    ),
    4: (
        "IMPLEMENTED",
        "README.md",
        "Requested module separation exists. Optional docker-compose is not necessary for the local artifact.",
    ),
    5: (
        "PARTIAL",
        "frontend/src/components/Workspaces.tsx",
        "Fifteen distinct roles. Every listed role feature is individually assessed below.",
    ),
    6: (
        "IMPLEMENTED",
        "backend/auth.py",
        "Stored organizations/users/roles, scope checks, commercial redaction, disabled-user checks and demo-only switching.",
    ),
    7: (
        "IMPLEMENTED",
        "backend/models/domain.py",
        "Every named entity and core field is mapped; extension tables preserve the original schema. Stored architecture fields are not automatically completed workflows.",
    ),
    8: (
        "IMPLEMENTED",
        "data/seed/network.py",
        "Four approximate Kerala anchors and three synthetic segments, source metadata and explicit operational assumptions. Historic NW-3 context is distinguished from present legal scope.",
    ),
    9: (
        "IMPLEMENTED",
        "backend/api/intake.py",
        "Text, typed, text/scanned PDF, PNG/JPEG, CSV/XLSX review and confirmation. Missing fields stay missing; invoice/BOQ support is generic extraction, not accounting interpretation.",
    ),
    10: (
        "PARTIAL",
        "intelligence/voice_intake/parser.py",
        "Recording/upload, STT adapter, native/transliterated/mixed variants, uncertainty and explicit fallback work. Real Malayalam provider accuracy/credentials remain untested.",
    ),
    11: (
        "PARTIAL",
        "intelligence/broker_agent/agent.py",
        "Bounded rank/modes/pool/backhaul tools plus intake; other possible tools exist as services/APIs rather than all being exposed to the agent. General model translation is not validated.",
    ),
    12: (
        "IMPLEMENTED",
        "feasibility/engine.py",
        "Weight, volume, draft, air draft, beam, category/co-load, terminals/resources, windows/locks, maintenance and certificates with reasons.",
    ),
    13: (
        "IMPLEMENTED",
        "optimization/matching/engine.py",
        "Configured BALANCED/CHEAPEST/FASTEST/GREENEST/MOST_RELIABLE profiles and visible factors; route is a hard filter and backhaul a separate preview.",
    ),
    14: (
        "IMPLEMENTED",
        "optimization/pooling/solver.py",
        "CP-SAT common-terminal pooling with capacity, volume, compatibility, deadlines, tonnage/revenue/handling objective. General route deviation is outside this restricted formulation.",
    ),
    15: (
        "IMPLEMENTED",
        "optimization/backhaul/search.py",
        "Reverse corridor/window/capacity/route/cargo validation and revenue estimate; only a booked return counts as avoided empty travel.",
    ),
    16: (
        "IMPLEMENTED",
        "optimization/terminal_selection/planner.py",
        "Configured terminal pairs, connecting roads, waiting, handling, hard vessel/resource constraints and deadline evaluation.",
    ),
    17: (
        "IMPLEMENTED",
        "backend/services/planning.py",
        "Full delivered cost, ETA, handoffs, SLA, risk/reliability and carbon; urgent road wins. Direct water is honestly unavailable for door pickup.",
    ),
    18: (
        "IMPLEMENTED",
        "optimization/multimodal/costs.py",
        "Configurable tonne-km factors with synthetic provenance; no certified emissions claim.",
    ),
    19: (
        "IMPLEMENTED",
        "backend/services/recurring.py",
        "Dated patterns/stops/weekdays/capacities, recurring approval, per-segment reservations, one-occurrence cancellation and demand proposals with insufficient-history labels.",
    ),
    20: (
        "PARTIAL",
        "backend/services/analytics.py",
        "Computed multiple quotes, price/reliability/ETA/risk comparison and comparable demo-rate history. Manual operator quote negotiation remains partial.",
    ),
    21: (
        "IMPLEMENTED",
        "backend/services/analytics.py",
        "Recorded completed voyages, durations, waits, cancellations, disruptions and on-time rate; score withheld below five completed voyages.",
    ),
    22: (
        "PARTIAL",
        "backend/services/bookings.py",
        "Transparent reliability/slack/cargo/handoff factors and LOW/MEDIUM/HIGH. Terminal/restrictions are hard feasibility gates; weather is a placeholder/read adapter rather than an active risk factor.",
    ),
    23: (
        "IMPLEMENTED",
        "backend/services/bookings.py",
        "Real request/booking/shipment state transitions, atomic reservations and forbidden skips. Failure/cancellation/replanning are persisted.",
    ),
    24: (
        "PARTIAL",
        "backend/services/recovery.py",
        "Eight pre-departure disruptions, later schedule/replacement/terminal/service/road alternatives, deltas, approval and atomic whole-pool recovery. Split loads and mid-voyage rescue remain roadmap.",
    ),
    25: (
        "PARTIAL",
        "backend/api/analytics.py",
        "Text reports, location/type/reporter/confidence/expiry, photos, VERIFIED/DISPUTED review and explicit restriction promotion. Voice report transcription/corroboration automation is not implemented.",
    ),
    26: (
        "PARTIAL",
        "backend/api/demo.py",
        "Deterministic road restriction, critical priority and labeled authority impact. Full emergency dispatch allocation and live flood observations are not connected.",
    ),
    27: (
        "IMPLEMENTED",
        "backend/services/analytics.py",
        "Historical CSV/XLSX replay, HIGH/MEDIUM/LOW classification and aggregate potential cost/carbon/trucks with reasons; not guaranteed conversion or historical navigation reconstruction.",
    ),
    28: (
        "IMPLEMENTED",
        "backend/services/analytics.py",
        "Search events and seven failure classes, corridor tonnage/frequency and unique request counts.",
    ),
    29: (
        "IMPLEMENTED",
        "backend/services/impact.py",
        "Nearby demand/supply, capabilities, road access, utilization and unserved demand in a disclosed advisory heuristic.",
    ),
    30: (
        "IMPLEMENTED",
        "backend/services/impact.py",
        "Persisted selected/completed booking metrics, per-cargo baseline, utilization, actual booked backhaul and demand gaps.",
    ),
    31: (
        "IMPLEMENTED",
        "backend/services/bookings.py",
        "Milestone positions/progress/timeline and ETA; simulated tracking is disclosed. Optional validated external read adapter exists.",
    ),
    32: (
        "IMPLEMENTED",
        "backend/services/documents.py",
        "All seven prototype data packages; statutory documents are not issued. Printable QR labels are additional HTML/SVG artifacts.",
    ),
    33: (
        "IMPLEMENTED",
        "frontend/src/components/Operator.tsx",
        "Profile/certificate validity and synthetic completed/on-time/cancellation/claim/reliability fields are visible, never represented as official verification.",
    ),
    34: (
        "IMPLEMENTED",
        "backend/api/demo.py",
        "Seed/reset, offline map/fallback, A–F scenarios and guided judge checkpoints use real services.",
    ),
    35: (
        "IMPLEMENTED",
        "scripts/generate_measured_results.py",
        "80 + 58 t = 138 t / 92%, 62 t return opportunity, rejection, booking, tracking and impact computed from fixtures.",
    ),
    36: (
        "IMPLEMENTED",
        "frontend/src/App.tsx",
        "Role navigation, responsive/mobile view, enterprise forms, statuses, loading/error/empty states and demo-only switcher.",
    ),
    37: (
        "IMPLEMENTED",
        "frontend/src/components/Planner.tsx",
        "Cargo/route/deadline, road/water/hybrid cards, recommendation, cost/SLA/carbon/source explanation.",
    ),
    38: (
        "IMPLEMENTED",
        "frontend/src/components/Operator.tsx",
        "Capacity, demand, utilization/pool projection, return opportunity and potential revenue with disclosed deterministic or configured-AI provenance.",
    ),
    39: (
        "IMPLEMENTED",
        "frontend/src/components/Government.tsx",
        "Map/heatmap, selected/completed impact, utilization/backhaul/unserved and corridor/terminal gaps.",
    ),
    40: (
        "IMPLEMENTED",
        "docs/SECURITY.md",
        "Prototype controls reviewed; production identity, retention, malware scanning and isolated upload workers remain explicit gaps.",
    ),
    41: (
        "IMPLEMENTED",
        "docs/TESTING.md",
        "Original and expanded meaningful unit/integration/browser checks; actual scanned-PDF OCR and transaction rollback covered.",
    ),
    42: (
        "IMPLEMENTED",
        "backend/repositories/common.py",
        "Structured event audits/logging; no credentials or uploaded bodies logged.",
    ),
    43: (
        "NOT APPLICABLE",
        "docs/CONTINUATION_PLAN.md",
        "Historical build order: continuation first audited and verified the existing baseline, then preserved P0/P1 while extending it.",
    ),
    44: (
        "PARTIAL",
        "docs/FUTURE_ROADMAP.md",
        "P0/P1 and substantial P2 work; production WhatsApp/payment/insurance/government/IoT/predictive maintenance intentionally remain P3.",
    ),
    45: (
        "IMPLEMENTED",
        "docs/AI_AND_OPTIMIZATION.md",
        "Deterministic extraction/heuristics are labeled; local OCR is actual recognition; no fabricated accuracy, trained ETA or fake integrations.",
    ),
    46: (
        "IMPLEMENTED",
        "docs/DATA_PROVENANCE.md",
        "Reasons, cost/score factors, source/demo labels, freshness and insufficient sample warnings.",
    ),
    47: (
        "PARTIAL",
        "docs/GITHUB_PUBLICATION.md",
        "Local code, locks, tests, screenshots, links, security and commits prepared. Public creation/push remains explicitly unperformed.",
    ),
    48: (
        "IMPLEMENTED",
        "README.md",
        "All required docs exist and are updated, plus coverage/provider/migration/publication guides.",
    ),
    49: (
        "IMPLEMENTED",
        "docs/HACKATHON_SUBMISSION.md",
        "Title, concise description, problem, solution, innovations, actual AI boundary, stack, readiness, demo, metrics and limitations.",
    ),
    50: (
        "IMPLEMENTED",
        "docs/PRESENTATION_OUTLINE.md",
        "Requested nine-slide outline; an actual slide deck was not requested in place of the outline.",
    ),
    51: (
        "IMPLEMENTED",
        "docs/DEMO_SCRIPT.md",
        "Three-minute manual story, optional guided checkpoints and failure fallback rehearsal.",
    ),
    52: (
        "IMPLEMENTED",
        "frontend/src/components/JudgeDemo.tsx",
        "Judge-facing WHY for failure, modes, pooling, benchmarks, fleet assignment and recovery with computed deltas.",
    ),
    53: (
        "IMPLEMENTED",
        "docs/TESTING.md",
        "Bounded optimizers, requests, OCR/PDF workers and imports; local offline mode. Production load/latency capacity is not certified.",
    ),
    54: (
        "IMPLEMENTED",
        "tests/integration/test_vertical_slice.py",
        "The sixteen required vertical-slice outcomes are tested using actual domain services and persisted records.",
    ),
    55: (
        "IMPLEMENTED",
        "docs/CONTINUATION_PLAN.md",
        "Action-oriented continuation, honest assumptions, bounded dependencies and documentation; no disconnected rebuild.",
    ),
    56: (
        "NOT APPLICABLE",
        "docs/CONTINUATION_PLAN.md",
        "Original first-action instructions were superseded by the continuation audit/baseline/preserve instructions, which were followed.",
    ),
}

ROLE_SOURCES = {
    "A": "frontend/src/components/Planner.tsx",
    "B": "frontend/src/components/Tracking.tsx",
    "C": "frontend/src/components/Workspaces.tsx",
    "D": "frontend/src/components/Evidence.tsx",
    "E": "frontend/src/components/Operator.tsx",
    "F": "frontend/src/components/Advanced.tsx",
    "G": "frontend/src/components/Tracking.tsx",
    "H": "backend/services/terminal_resources.py",
    "I": "frontend/src/components/Advanced.tsx",
    "J": "frontend/src/components/Workspaces.tsx",
    "K": "feasibility/compliance/checks.py",
    "L": "backend/api/operations.py",
    "M": "backend/api/analytics.py",
    "N": "backend/services/impact.py",
    "O": "backend/api/admin.py",
}
ROLE_PARTIAL = {
    "A": {
        "preferred operators": "Stored CargoPreference field only; no management/ranking preference UI.",
        "AI extraction into structured cargo data": "Adapter and schema validation work; external credentials were not available.",
        "recurring capacity contract architecture": "Capacity holds and agreed rates work; legal negotiation/invoicing is not connected.",
    },
    "B": {
        "live/demo tracking": "Demo tracking works; external provider adapter is separate from the map.",
        "cargo readiness": "Warehouse records readiness; no physical sensor verification.",
    },
    "C": {
        "loading equipment requirement": "Terminal capability/resource checks enforce requirements; a dedicated warehouse equipment checklist is not exposed."
    },
    "D": {
        "unloading window": "ETA/status and assigned tracking are visible; a dedicated planned unloading-window card is not exposed.",
        "OTP/signature architecture": "Secure local demo OTP works when requested; older milestone-only deliveries remain unverified. Receipt names are not legal signatures.",
    },
    "E": {
        "AI cargo recommendations": "Feasible recommendations work locally; real external model validation is pending.",
        "quote management": "Automatic computed quotes/opportunities; no commercial negotiation editor.",
        "demand heatmap": "Network aggregate exists, but the operator view uses opportunity cards rather than a dedicated demand heatmap.",
        "rate benchmark": "Shipper benchmark works; operator-specific benchmark UI is not yet exposed.",
    },
    "F": {
        "vessel fleet map": "Voyage tracking/network map exists; a dedicated all-vessel current-position map is not implemented.",
        "assign vessel": "Fleet previews assignments; dispatch/control/admin approve consequential bookings.",
        "vessel repositioning": "One-voyage optimizer includes graph reposition distance/readiness; no multi-tour relocation dispatch.",
        "route alerts": "Restrictions and recovery are visible; no push notification feed.",
        "replacement vessel": "Dispatch/control approval workflow; fleet can view but cannot override recovery authorization.",
    },
    "G": {
        "position update": "Milestone simulation and optional read adapter; manual GPS capture/live map ingestion not connected.",
        "weather field architecture": "Validated adapter/read endpoint exists; captain weather card and authoritative safety rule remain extensions.",
        "navigation notices": "Configured restrictions and reviewed observations; official notice feed not connected.",
        "offline-friendly design": "Cached labeled read view and local map; disconnected writes/synchronization remain roadmap.",
    },
    "H": {
        "gate status": "Appointment starts EXPECTED and warehouse gate-out can be recorded; full gate lifecycle editing/scanning is not implemented.",
        "storage availability": "Capacity enforced during handling reservations; long-term warehouse inventory occupancy is not modeled.",
    },
    "I": {
        "on-track": "Timeline/risk board provides status; dedicated per-SLA on-track counters remain partial.",
        "delayed": "Risk and recovery/delay records exist; automatic lateness monitoring is not running.",
        "carrier/operator scorecards": "Synthetic profile metrics and corridor analytics; no dedicated 3PL scorecard comparison.",
        "cost analytics": "Per-booking cost and fleet/impact calculations; a dedicated cost trend dashboard is not implemented.",
        "SLA analytics": "Plan SLA and actual on-time corridor metrics; contract-specific SLA penalty reporting remains roadmap.",
    },
    "J": {
        "escrow architecture": "Payment contract/prototype states only; no held funds or real escrow."
    },
    "K": {
        "operator verification": "Platform demo certificate/organization verification; no legal identity/authenticity integration.",
        "pre-voyage checklist": "Computed compliance/feasibility checks; a separate signed checklist document is not implemented.",
    },
    "L": {},
    "M": {
        "lock status architecture": "Configured lock hours and deterministic waits; no live gates/authority bookings.",
        "traffic": "Vessel states and queues are available; full waterway traffic monitoring/map layers are not implemented.",
        "navigation alerts": "UI restrictions/observations; no external notice ingestion or push alerts.",
    },
    "N": {},
    "O": {
        "verification": "Prototype certificate/organization records; no production identity/document authenticity workflow."
    },
}


def link(path):
    return f"[{path}](../{path})"


def render():
    catalog = json.loads(
        (ROOT / "data/sources/specification_feature_catalog.json").read_text(
            encoding="utf-8"
        )
    )
    rows = [
        "# Feature audit",
        "",
        "Reviewed against both user-supplied specifications on 7 October 2026. **Everything in the broad master prompt is not production-complete.** P0/P1 and the highest-value continuation workflows are implemented; the exact partial/roadmap boundaries are below. IMPLEMENTED means working in the documented synthetic prototype scope, not certified real-world deployment.",
        "",
        "Statuses: IMPLEMENTED = an executable prototype workflow or satisfied artifact requirement; PARTIAL = working subset/interface with a stated gap; ROADMAP = no connected workflow; NOT APPLICABLE = context/historical/optional instruction rather than a current software feature. Missing/broken baseline gaps are resolved or represented by these final statuses, without silently calling architecture a completed integration.",
        "",
        "## Baseline and verification",
        "",
        "Before edits: clean commit `179470f`, 41 backend tests, 9 browser tests and production build passed. The first sandboxed esbuild invocation could not spawn; the authorized retry passed. The original architecture and vertical slice were preserved. Final results are recorded in [Testing](TESTING.md). No external AI/STT credentials or production connectors were tested. Existing origin points to Dony-sunny/keralAI_hack; this continuation made no push or repository creation, and remote visibility/content was not verified.",
        "",
        "## All 56 master sections",
        "",
        "| Section | Status | Source | Scope / remaining boundary |",
        "|---|---|---|---|",
    ]
    for section in catalog:
        status, source, note = SECTION[section["number"]]
        rows.append(
            f"| {section['number']}. {section['title']} | {status} | {link(source)} | {note} |"
        )
    for section in catalog:
        number = section["number"]
        if number == 5:
            rows.extend(
                [
                    "",
                    "## Every master role feature",
                    "",
                    "Each row preserves the supplied feature wording. Additional continuation implementations are assessed in the phase matrix below.",
                ]
            )
            for role in section["roles"]:
                letter = role["letter"]
                rows.extend(
                    [
                        "",
                        f"### {letter}. {role['title']}",
                        "",
                        "| Feature | Status | Source / scope |",
                        "|---|---|---|",
                    ]
                )
                for feature in role["features"]:
                    note = ROLE_PARTIAL.get(letter, {}).get(feature)
                    rows.append(
                        f"| {feature} | {'PARTIAL' if note else 'IMPLEMENTED'} | {link(ROLE_SOURCES[letter])}. {note or 'Working in the disclosed prototype scope; see workspace coverage for the exact user action.'} |"
                    )
            continue
        if not section["features"]:
            continue
        rows.extend(
            [
                "",
                f"### Master {number}: listed requirements",
                "",
                "| Feature / requirement | Status | Source / scope |",
                "|---|---|---|",
            ]
        )
        for feature in section["features"]:
            status, source, note = SECTION[number]
            if number == 1 and feature in {
                "clear project title",
                "concise project description",
                "problem → ideation → artifact progression",
                "working software artifact",
                "project documentation",
                "project presentation",
            }:
                status = "IMPLEMENTED"
                source = "docs/HACKATHON_SUBMISSION.md"
                note = "Requested local artifact/content exists; presentation scope is the supplied nine-slide outline."
            elif number == 1 and feature in {
                "GitHub repository",
                "clean submission readiness",
            }:
                status = "PARTIAL"
                source = "docs/GITHUB_PUBLICATION.md"
                note = "Local changes and publication commands prepared; this continuation performed no repository creation or remote push."
            elif number in {1, 43, 56}:
                status = "NOT APPLICABLE"
                note = "Context or process requirement; implementation/artifact scope is assessed in the section matrix."
            elif number == 44:
                if any(
                    term in feature.lower()
                    for term in ["whatsapp", "predictive", "iot"]
                ):
                    status = "ROADMAP"
                elif any(
                    term in feature.lower()
                    for term in [
                        "production payment",
                        "insurance provider",
                        "government workflow",
                    ]
                ):
                    status = "PARTIAL"
                    source = "backend/services/connectors.py"
                    note = (
                        "Typed no-op/provider contract only. Prototype / Not connected."
                    )
                else:
                    status = "IMPLEMENTED"
                    note = "Working prototype; individual limits are documented in the section matrix."
            elif number in {9, 10, 11, 20, 24, 25, 26, 47}:
                status = "PARTIAL" if number in {10, 11, 20, 24, 25, 26, 47} else status
            if "docker-compose" in feature:
                status = "NOT APPLICABLE"
                note = "Optional container file; local setup scripts are the verified launch path."
            rows.append(
                f"| {feature.replace('|', '/')} | {status} | {link(source)}. {note} |"
            )
    rows.extend(
        [
            "",
            "## Continuation phase coverage",
            "",
            "| Phase | Status | Source / result |",
            "|---|---|---|",
        ]
    )
    phases = [
        (
            0,
            "IMPLEMENTED",
            "docs/CONTINUATION_PLAN.md",
            "Code audit, baseline before edits and prioritized preservation plan.",
        ),
        (
            1,
            "PARTIAL",
            "intelligence/provider/llm.py",
            "Three clean provider classes, diagnostics, timeout/malformed/retry mocks and fallback; real credentials unavailable.",
        ),
        (
            2,
            "PARTIAL",
            "intelligence/voice_intake/parser.py",
            "Mic/upload/STT path and varied Malayalam/mixed phrases with confirmation; real provider speech evaluation pending.",
        ),
        (
            3,
            "IMPLEMENTED",
            "intelligence/document_intake/ocr_worker.py",
            "Actual local scanned PDF/PNG/JPEG OCR, text first, bounded workers, metadata fields/review. Malayalam OCR is not validated; invoices/BOQ use generic extraction.",
        ),
        (
            4,
            "IMPLEMENTED",
            "intelligence/document_intake/spreadsheets.py",
            "XLSX/template, deterministic aliases, per-row errors/warnings, formula/duplicate-header limits, valid-only atomic import and error download.",
        ),
        (
            5,
            "IMPLEMENTED",
            "backend/services/evidence.py",
            "Private safe image evidence, uploader/timestamp/category, role workspaces and admin dispute view. Prototype DB storage, not production object storage.",
        ),
        (
            6,
            "IMPLEMENTED",
            "backend/services/evidence.py",
            "128-bit opaque cargo/booking/shipment QR references, printable labels and authorized hash navigation; no public commercial payload.",
        ),
        (
            7,
            "PARTIAL",
            "backend/services/evidence.py",
            "Salted expiring single-use local OTP with receiver identity, five attempts and issuance limits. Requesting a challenge enforces verification; legacy demo milestone delivery remains explicitly unverified. No legal signature or SMS.",
        ),
        (
            8,
            "IMPLEMENTED",
            "backend/services/recurring.py",
            "Dated patterns, segment occupancy, recurring booking, cancellation and suggested-service evidence labels.",
        ),
        (
            9,
            "IMPLEMENTED",
            "optimization/fleet.py",
            "Bounded multi-vessel/cargo CP-SAT, five objective profiles, hard combined validation and atomic approval. One voyage per vessel, not full multi-tour VRP.",
        ),
        (
            10,
            "IMPLEMENTED",
            "backend/services/terminal_resources.py",
            "Berth/equipment/storage/gate capacity checks, queue/alternate slots, appointments and handling/delay records; fixed handling duration and prototype storage intervals.",
        ),
        (
            11,
            "PARTIAL",
            "backend/services/recovery.py",
            "Eight disruption types, affected-only replanning, replacement/later/service/terminal/road alternatives, deltas and whole-pool approval. No split-load or mid-voyage recovery.",
        ),
        (
            12,
            "IMPLEMENTED",
            "backend/services/analytics.py",
            "Corridor actual milestone aggregates, voyage deduplication, insufficient-sample score and disruption/cancellation counts.",
        ),
        (
            13,
            "IMPLEMENTED",
            "backend/services/analytics.py",
            "Comparable corridor/class/weight/time rates, source/sample size and minimum three observations; synthetic history is labeled, not industry rates.",
        ),
        (
            14,
            "IMPLEMENTED",
            "backend/api/analytics.py",
            "Confidence/expiry, photos and VERIFIED/DISPUTED review with explicit restriction promotion; observation review is not official authority verification.",
        ),
        (
            15,
            "IMPLEMENTED",
            "backend/services/recurring.py",
            "Commercial fields, reserved service capacity, contract draws and applied agreed water rate; legal negotiation/settlement penalties are not implied.",
        ),
        (
            16,
            "IMPLEMENTED",
            "backend/services/analytics.py",
            "Historical road CSV/XLSX suitability and potential aggregates; replay uses current demo availability, not reconstruction of historical safety.",
        ),
        (
            17,
            "IMPLEMENTED",
            "backend/services/analytics.py",
            "Seven failure reasons, unique tonnage/frequency and price rejection.",
        ),
        (
            18,
            "IMPLEMENTED",
            "backend/api/admin.py",
            "Organization/user creation, role assignment/change, disable, membership and audits; stored signed identities retained.",
        ),
        (
            19,
            "PARTIAL",
            "docs/WORKSPACE_COVERAGE.md",
            "Fifteen roles audited; reused data for crew, gate/loading, handling, appointments, evidence, payment/disputes and admin. Remaining secondary gaps explicitly listed above.",
        ),
        (
            20,
            "IMPLEMENTED",
            "backend/services/connectors.py",
            "Demo/external validated tracking interface with freshness/fallback; optional read endpoint, no live AIS claim.",
        ),
        (
            21,
            "IMPLEMENTED",
            "backend/services/connectors.py",
            "Demo/external weather interface, schema/freshness/location fallback; no automatic hard-safety override or IMD claim.",
        ),
        (
            22,
            "IMPLEMENTED",
            "backend/services/connectors.py",
            "Requested interface-only payment/insurance/government contracts, demo/no-op defaults, visible Not connected states.",
        ),
        (
            23,
            "IMPLEMENTED",
            "docs/POSTGRESQL_MIGRATION.md",
            "Model review, driver/URL/migration/concurrency/deployment plan; SQLite retained. PostgreSQL deployment/Alembic rehearsal is still roadmap.",
        ),
        (
            24,
            "IMPLEMENTED",
            "docs/SECURITY.md",
            "Signed identity maintained, future verification interface and OIDC/OAuth2/SSO mapping documented; no heavy identity service introduced.",
        ),
        (
            25,
            "PARTIAL",
            "docs/GITHUB_PUBLICATION.md",
            "Secrets/links/screenshots/checks/readiness and exact commands; no public creation or push without approval.",
        ),
        (
            26,
            "IMPLEMENTED",
            "scripts/generate_measured_results.py",
            "Actual services in isolated databases generate all requested metrics and separate direct-water/road-wins/return/recovery/recurrence/fleet cases.",
        ),
        (
            27,
            "IMPLEMENTED",
            "frontend/src/components/JudgeDemo.tsx",
            "Demo-only clean checkpoints, approvals, reset and computed evidence; actual app services.",
        ),
        (
            28,
            "IMPLEMENTED",
            "backend/api/judge.py",
            "Guided flagship from confirmed intake to pool/booking/optional whole-pool recovery/departure/impact, with manual screens preserved.",
        ),
        (
            29,
            "IMPLEMENTED",
            "frontend/src/components/JudgeDemo.tsx",
            "Readable failure, score, price, utilization, benchmark, fleet and recovery explanations with synthetic-source labels.",
        ),
        (
            30,
            "IMPLEMENTED",
            "docs/FEATURE_AUDIT.md",
            "All requested docs updated; this catalog covers all master sections, role features, listed requirements and continuation phases.",
        ),
        (
            31,
            "IMPLEMENTED",
            "docs/TESTING.md",
            "Acceptance tests for new boundaries plus all original tests; actual PDF renderer, capacity/compatibility, authorization and rollback tested.",
        ),
        (
            32,
            "IMPLEMENTED",
            "docs/KNOWN_LIMITATIONS.md",
            "Workload/timeout bounds, best feasible solver status, loading/errors and atomic writes; production stress certification remains out of scope.",
        ),
        (
            33,
            "IMPLEMENTED",
            "docs/TESTING.md",
            "Final local gate is recorded after running original/extended tests, build, measured cases, offline/failure checks, reset, links and security review.",
        ),
    ]
    rows += [
        f"| {n} | {status} | {link(source)}. {note} |"
        for n, status, source, note in phases
    ]
    rows.extend(
        [
            "",
            "The catalog is a checked-in extraction of the supplied master feature lists, not a claim that test counts prove every production integration. Re-render with `python scripts/update_feature_audit.py`. Remaining production requirements are expanded in [Known limitations](KNOWN_LIMITATIONS.md), [Roadmap](FUTURE_ROADMAP.md), [Provider setup](PROVIDER_SETUP.md) and [Publication](GITHUB_PUBLICATION.md).",
            "",
        ]
    )
    (ROOT / "docs/FEATURE_AUDIT.md").write_text("\n".join(rows), encoding="utf-8")


if __name__ == "__main__":
    render()
