# Judge Q&A

**Why does this need AI?** Freight arrives as local-language voice, invoices, purchase orders and informal descriptions. A configurable model can interpret that content and select broker tools. Default venue fallback is openly deterministic. Hard constraints and arithmetic remain operational truth.

**Why isn't this just a marketplace?** A listing alone cannot prove draft/bridge/terminal/schedule feasibility, compute full delivered cost, create compatible pools and return loads, reserve capacity or manage execution/recovery. Those steps are connected in actual records.

**Why can't an ordinary road platform solve it?** The implemented domain is water-specific: loaded draft, air draft, waterway segments, lock windows, jetty/approach capabilities and vessel certificates. Avoid claiming unsupported facts about named competitors' current capabilities; explain this prototype's concrete domain difference.

**Why use an LLM?** To lower intake friction and interpret unstructured multilingual freight communication, and to select approved tools. It does not calculate prices or supply physical navigation values.

**How do you prevent hallucination?** Untrusted extraction enters Pydantic, missing fields remain null, user confirms, and deterministic services own route/safety/totals. Only feasible vessels can enter recommendations. A broker cannot turn a tool FAIL into PASS or automatically approve a booking.

**What if internet/API fails?** The main flow has local seeds, rule-based extraction, a disclosed sample voice transcript, local optimizers and an offline schematic map. The local API still needs to run; fully disconnected captain writes are a roadmap item.

**What data is real?** NW-3 and terminal context is sourced to IWAI. Operational depths, clearances, vessels, cargo, tariffs, reliability, schedules and emissions factors are synthetic. DATA_PROVENANCE.md distinguishes every class; no live feed is claimed.

**What happens when water isn't best?** Feasible modes compete on full delivered cost and deadlines. Urgent cargo tests demonstrate road winning. Direct water does not omit pickup/last-mile costs; those are included in hybrid.

**What is optimized?** CP-SAT selects compatible pools and multi-vessel cargo assignments under capacity, volume, corridor and deadline constraints. Fleet assignment permits one voyage per vessel, serves feasible tonnage first, then applies the selected objective. Backhaul searches reverse availability; terminal pairs/resources, dated services and contract segment holds are deterministic. No trained ML optimizer or full multi-tour VRP is claimed.

**How do you make money?** Possible transaction fee, operator subscription, 3PL enterprise SaaS and scheduled-service analytics. The demo payment states do not transfer money; commercial viability needs a pilot.

**How does government benefit?** Actual platform bookings produce selected/completed modal shift, estimated savings/emissions, utilization and booked backhaul, while requests and rejected matches expose unmet demand. Activation scores are advisory, not official investment decisions.

**What about dangerous goods?** They are a compliance validation problem. Vessel category/certification, verified dangerous-goods certificate and compatible terminals must pass. Synthetic verification is not a legal endorsement; real deployment needs applicable authorized review.

**Can you handle disruptions?** Eight pre-departure types include equipment failure, late trucks, cargo readiness, cancelled services and reduced capacity. Revalidated later/terminal/service/vessel/road options expose SLA/cost/ETA deltas, and users can approve an entire pool atomically. Mid-voyage intervention and split loads remain roadmap.

**How do we reproduce the numbers?** Reset, pool and book, then inspect government metrics; or run scripts/generate_measured_results.py. The hero computes 138 t/92%, ₹27,857.40 pooled cost difference, 723.66 kg estimated CO₂ difference and seven equivalent long-haul movements. Inputs/factors are synthetic; an empty transaction set reports zero impact. Return suggestions count only after booking.

**Is everything in the large specification done?** No production-completeness claim is made. FEATURE_AUDIT.md preserves all 56 master sections, individual role features, 647 listed requirements and all continuation phases with implementation sources. Preferred-operator management, negotiation, some secondary dashboards, split/mid-voyage recovery and production integrations remain partial/roadmap. The continuation's highest-value prototype work and final local verification are documented.

**Does document recognition work offline?** Actual local ONNX OCR handles the generated English scanned PDF/PNG; text PDFs are attempted first. Invoice/PO/BOQ fields are reviewed, not legal/accounting interpretation. Timeouts, page/pixel limits, confidence caveats and missing fields are visible. XLSX import also works locally and never evaluates formulas.

**Is delivery legally verified?** Local demo OTP records receiver identity, expiry and single-use verification; requesting it gates delivery. Preserved milestone-only deliveries remain unverified. Photo/name/quantity records are prototype evidence, not a legal digital signature or connected SMS service.
