# Known limitations

The P0 flow and P1 optimizers execute real application logic, but this is a hackathon prototype.

- All operational depths, dimensions, tariffs, storage/equipment, reliability history, certificates and emissions factors are synthetic. PASS means only “passed configured demo constraints.” Not a navigation aid or legal compliance certification.
- The graph has four approximate Kerala nodes and three bidirectional segments. It does not represent the full present NW-3 legal extent, surveyed geometry, tide-dependent depth, bridge operations or real lock bookings.
- Road distance is haversine × 1.35; speeds, handling/waiting and turnaround are transparent assumptions. No live ETA/weather/traffic model or statistically trained reliability estimator exists.
- Default intake is a narrow deterministic parser, not AI/ML. Configurable LLM/multimodal and STT paths are implemented but untested with real credentials. Unrecognized fields require review. Scanned PDFs need OCR; XLSX import is architecture, while CSV preview works.
- Terminal slots assume one conservative berth and fixed handling duration. Multi-berth equipment crews, actual gate appointments and lock reservations are roadmap work.
- Pooling solves compatible loads in a common terminal corridor. General multi-stop vessel routing, partial cargo splitting and full fleet VRP are not implemented. Cross-tenant pools require control-tower coordination; shippers cannot approve competitors' cargo.
- Scheduled services model a concrete departure instance with a recurrence label, not a calendar generator. Aggregate demand proposals do not demonstrate recurring-demand evidence.
- Recovery is pre-departure. It recalculates individual cargo plans and requires approval; complex mid-voyage transshipment, location-aware rescue and whole-pool replanning are not implemented.
- Tracking positions are simulated milestone-based waypoints. No live GPS feed or electronic signature/OTP verification is connected. Receipt names are prototype acceptance records. Photo storage, QR generation and offline write synchronization are architectural extension points.
- Documents are JSON data packages, not official government documents, certified manifests, tax invoices or e-way bills. Payment states do not move funds; escrow, real settlements and insurance APIs are roadmap items.
- Role workspaces implement core operational tasks; advanced peripheral features are explicitly listed in WORKSPACE_COVERAGE.md. Production SSO, user onboarding and granular organization policy administration are not completed.
- SQLite is appropriate for the local demo. PostgreSQL requires driver/migrations/production concurrency tests. Upload work should move to a sandboxed resource-limited worker in production.
- The software artifact, docs and screenshots are local. A public GitHub remote, presentation slide file and hosted deployment are not published. The requested 9-slide outline and submission text are included.
