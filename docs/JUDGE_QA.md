# Judge Q&A

**Why does this need AI?** Freight arrives as local-language voice, invoices, purchase orders and informal descriptions. A configurable model can interpret that content and select broker tools. Default venue fallback is openly deterministic. Hard constraints and arithmetic remain operational truth.

**Why isn't this just a marketplace?** A listing alone cannot prove draft/bridge/terminal/schedule feasibility, compute full delivered cost, create compatible pools and return loads, reserve capacity or manage execution/recovery. Those steps are connected in actual records.

**Why can't an ordinary road platform solve it?** The implemented domain is water-specific: loaded draft, air draft, waterway segments, lock windows, jetty/approach capabilities and vessel certificates. Avoid claiming unsupported facts about named competitors' current capabilities; explain this prototype's concrete domain difference.

**Why use an LLM?** To lower intake friction and interpret unstructured multilingual freight communication, and to select approved tools. It does not calculate prices or supply physical navigation values.

**How do you prevent hallucination?** Untrusted extraction enters Pydantic, missing fields remain null, user confirms, and deterministic services own route/safety/totals. Only feasible vessels can enter recommendations. A broker cannot turn a tool FAIL into PASS or automatically approve a booking.

**What if internet/API fails?** The main flow has local seeds, rule-based extraction, a disclosed sample voice transcript, local optimizers and an offline schematic map. The local API still needs to run; fully disconnected captain writes are a roadmap item.

**What data is real?** NW-3 and terminal context is sourced to IWAI. Operational depths, clearances, vessels, cargo, tariffs, reliability, schedules and emissions factors are synthetic. DATA_PROVENANCE.md distinguishes every class; no live feed is claimed.

**What happens when water isn't best?** Feasible modes compete on full delivered cost and deadlines. Urgent cargo tests demonstrate road winning. Direct water does not omit pickup/last-mile costs; those are included in hybrid.

**What is optimized?** CP-SAT selects compatible binary load memberships under integer weight/volume, terminal-corridor and deadline constraints. Backhaul searches reverse availability. Terminal pairs and scheduled-service segment capacity are evaluated deterministically. We do not claim a trained ML optimizer.

**How do you make money?** Possible transaction fee, operator subscription, 3PL enterprise SaaS and scheduled-service analytics. The demo payment states do not transfer money; commercial viability needs a pilot.

**How does government benefit?** Actual platform bookings produce selected/completed modal shift, estimated savings/emissions, utilization and booked backhaul, while requests and rejected matches expose unmet demand. Activation scores are advisory, not official investment decisions.

**What about dangerous goods?** They are a compliance validation problem. Vessel category/certification, verified dangerous-goods certificate and compatible terminals must pass. Synthetic verification is not a legal endorsement; real deployment needs applicable authorized review.

**Can you handle disruptions?** Pre-departure cancellation/closure triggers revalidation and alternative plans. Users approve consequential recovery. Mid-voyage intervention and coordinated whole-pool recovery require further operational design.

**How do we reproduce the numbers?** Reset, pool and book the fixture, then inspect government metrics; or run scripts/measure_demo.py. A blank transaction set reports zero shifted tonnes/impact. Return suggestions do not count as avoided empty voyages until actually booked.
