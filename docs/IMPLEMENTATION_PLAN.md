# Implementation checklist

Build one platform in the prescribed risk-reducing order. No external credentials are required for the deterministic demo. P3 integrations remain explicitly documented architecture.

1. Repository, FastAPI, SQLAlchemy/SQLite, React/Vite skeleton, transparent seeds.
2. Validated manual cargo and vessel creation, tenant ownership.
3. Waterway graph, vessel/cargo/terminal/compliance hard feasibility.
4. Configurable deterministic ranking with rejected-candidate explanations.
5. Transactional booking, reservations, shipment state machine. Verify the vertical slice before continuing.
6. Shipper decision screen, operator workspace, control tower.
7. Provider abstraction; text/PDF intake; review missing fields before persistence.
8. Malayalam/transliterated voice/text intake; recording/upload; disclosed demo transcript fallback.
9. Door-to-door road/water/hybrid comparison; configurable costs/carbon/SLA.
10. OR-Tools compatible load pooling, capacity/deadline/volume constraints.
11. Backhaul with reverse route and availability windows.
12. Evaluate terminal pairs including capability, access, waiting and cost.
13. Scheduled services, stops, segment capacity and demand-driven proposals.
14. Simulated positions, actual milestones, manifests and delivery documentation.
15. Booking-derived authority impact, unmet demand, corridor/terminal views.
16. Cancellation/route closure recovery; require explicit approval to rebook.
17. All 15 role workspaces, operational actions and architecture for advanced integrations.
18. Critical unit/integration/browser tests, security review, polished responsive UI, all required documentation and submission assets.

## P0 acceptance

Persist cargo and vessel availability → reject unsafe candidates → rank feasible options → compare modes → confirm booking → see and advance a real shipment. Every step has an API and UI path. Tenant isolation and reservation conflicts are tested.

## P1 acceptance

Pool 80 + 58 tonnes on a 150-tonne vessel (92% utilization), identify a feasible return load, book scheduled capacity safely, track demo positions, aggregate actual application records into impact metrics.

## Constraints

Infrastructure measurements, rates, reliability and emission factors are synthetic and carry provenance. Live navigation, government workflows, payments, production identity and offline map tiles are not connected. LLMs cannot override feasibility, compute totals or authorize bookings.

## Completed validation

All 18 phases have a working prototype component or an explicitly documented advanced-feature boundary. P0 and P1 acceptance flows pass. 41 backend tests, 9 browser tests and the production frontend build pass. The role coverage matrix, sample PDFs/CSV, generated measured results, screenshots, CI and required submission documents are present. Publishing a remote repository/hosted service and production integrations remain external deployment steps.
