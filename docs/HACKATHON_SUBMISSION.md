# Hackathon submission content

**Project title:** Jalayatra AI — Agentic Inland Freight Exchange for Kerala

**Short description (under 500 characters):**

Jalayatra AI turns cargo descriptions, documents and Malayalam operator availability into executable Kerala inland-freight plans. It validates vessel, waterway and terminal constraints, compares complete road/water/hybrid costs, pools compatible cargo, finds return loads and manages bookings, tracking and impact. A stable offline-friendly demo works without API credentials; all synthetic operational data and estimated impact are clearly labeled.

**Problem:** Cargo demand and vessel capacity are fragmented. Visibility alone does not establish physical feasibility, terminal readiness, connecting-road economics, load utilization or execution. Real deployments need trusted operational data and clear stakeholder responsibilities.

**Solution:** One digital freight twin and role-based workspaces connect understanding → validated planning → approval → booking → shipment → recovery → network evidence. The five challenge capabilities are implemented: cargo posting, vessel availability, matching recommendations, schedule planning and cost comparison.

**Core innovations:**

1. Reviewed document/text and Malayalam voice/transcript intake with a disclosed fallback.
2. Deterministic end-to-end physical, terminal, schedule and compliance feasibility.
3. OR-Tools compatible pooling plus return-window backhaul search.
4. Full road/water/hybrid delivered cost, SLA and transparent carbon estimates.
5. Recurring dated services, segment-capacity contracts, multi-vessel assignment and resource calendars.
6. Application-record impact, typed failed demand, corridor/rate samples, historical modal-shift opportunities and reviewed navigation observations.

**AI usage:** Optional LLM structured/multimodal extraction and bounded broker function calling; configurable Malayalam STT. Default local mode uses deterministic rules and orchestration, openly labeled. Safety constraints, totals and optimization are never delegated to the LLM. No fake model accuracy or trained ETA claim.

**Tech stack:** React, TypeScript, Vite, Leaflet/optional OpenStreetMap, Recharts, Python/FastAPI, Pydantic, SQLAlchemy/SQLite, OR-Tools CP-SAT, Dijkstra, pypdf/pypdfium2, RapidOCR ONNX, openpyxl, Pillow/qrcode and configurable HTTP AI/STT adapters.

**GitHub readiness:** Git repository, coherent modules, ignored secrets/runtime/build output, locked frontend dependencies, setup/reset scripts, automated CI, backend/browser tests, screenshots, API/architecture/provenance/security docs. Remote publishing remains an organizer/user account action; no fictional repository URL is supplied.

**Demo flow:** Operator transcript review → structured cargo → hard rejection → delivered-cost comparison → 138 t/92% pool → 62 t return opportunity → approved booking → actual shipment states → record-derived government metrics. Independent cancellation, route closure and flood scenarios are available.

**Impact metrics:** Confirmed and completed tonnes shifted, equivalent long-haul truck movements, estimated delivered-cost difference, prototype CO₂ difference, vessel utilization, booked backhaul matches and unserved demand. Metrics arise from application bookings, not manually entered impressive numbers. Use `data/demo/measured-results.json` for the reproducible measured fixture result.

**Limitations:** Synthetic operational data/factors, approximate graph/roads, simulated map positions, narrow local parser, external credentials untested, English demo OCR only, one-voyage fleet assignment, pre-departure recovery, prototype OTP/evidence/contracts and unconnected commerce/government/SSO. See the full feature audit, provenance and known limitations. Exact publication commands are prepared; no public repository or hosted URL is fabricated.

**Challenge context:** User-provided KeralAI Grand Challenge 2026 Kochi / Challenge 7 context. No verified official numerical judging weights are claimed. Working software, repository quality, documentation and demo reliability are treated as primary deliverables.
