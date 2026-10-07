# Current implementation compared with agent.md

Reviewed on 7 October 2026 against the current local source and the four release gates in [agent.md](../agent.md).

**Verdict: this is a useful, substantial prototype, but it does not yet meet the full target demo defined in agent.md. None of D1–D4 is complete.** Existing feasibility, authorization, optimization and offline workflows provide a foundation worth extending. Passing the existing test suite does not establish the newer financial, shared-voyage, quote-acceptance and provider-job requirements.

| Gate | Current position | Missing acceptance behavior |
| --- | --- | --- |
| D1: whole-trip costs and sailing contribution | Partial foundation: complete-mode line items, cost totals, synthetic source labels and an urgent road-winning test exist. | Costs remain linear per tonne/distance. No minimum/fixed truck-trip tariff, volume/piece-based trip calculation, fixed sailing cost, shared handling setup allocation, provider-payable contribution model or computed crossover ranges. |
| D2: voyage owns shared resources | Partial: pool identifiers, combined feasibility, segment capacity and resource calendars exist. The normal pooled resource path retains reservations when its first member cancels. | Scheduled departures can lose shared berths after a member cancels. Individual pooled delivery ETAs, aggregate vessel state and current utilization are incorrect in reproduced cases. No complete shared-voyage lifecycle, receiving-window model, cutoff or funded/dependent service commitment policy. |
| D3: accepted quote version and rate cards | Partial foundation: simple stored TransportQuote records, booking snapshots and itemized invoice drafts exist; tenant access is enforced. | Booking accepts an unbound boolean and recomputes prices. No immutable accepted quote version with cargo revision/validity, versioned terminal cards, amendment approvals or decimal/minor-unit finance. |
| D4: resource jobs and provider/operator acceptance | Partial foundation: route legs, manual truck appointments and operating records exist. | No assignment per required truck, vehicle volume/piece/lift model, persisted provider-job acceptance/decline/expiry bundle, or departure operator acceptance bound to the reviewed plan. Customer confirmation occurs before these acceptances. |

The statuses describe reusable foundations, not passing gate acceptance. Since D1 is incomplete, even the guide's D1-only fallback is not currently established. The older documented prototype demo can still be presented with its existing assumptions and limitations.

Acceptance-by-acceptance comparison:

| Guide acceptance | Assessment of current implementation |
| --- | --- |
| D1: 80 t requires at least four 20 t truck trips | Missing. The payload constant is used for impact equivalents, not for tariff calculation or truck assignments. |
| D1: fixed sailing/handling costs appear once | Missing. Current costs are tonne/distance/quantity based; there is no shared fixed-cost allocation ledger. |
| D1: line items and allocations reconcile | Partial. Existing quote line items sum correctly, as verified by `test_cost_totals_and_carbon`; shared allocations and consistent decimal finance are absent. |
| D1: high-fill loss-making sailing is identified | Missing. Neither provider payables nor modeled voyage contribution is calculated. |
| D1: computed crossover ranges, including no crossover | Missing. There is no feasible-scenario crossover calculation. |
| D1: urgent cargo can select road | Working for the configured prototype assumptions; `test_urgent_cargo_honestly_recommends_road` passed. |
| D2: first-member cancellation retains common resources | Working on the ordinary pool; failing on separately booked members of one scheduled departure. Both paths were reproduced. |
| D2: current tonnage and contribution update | Partial/failing. Active water tonnes update, but stored pool tonnage/utilization stay stale; contribution is absent. |
| D2: each load retains its door ETA | Failing. The anchor's combined ETA overwrites another member's final-road ETA. |
| D2: capacity/calendar conflicts cannot overbook | Partial foundation. Serialized SQLite booking and existing capacity tests pass; cancellation can still release a needed scheduled berth. |
| D2: final scheduled times undergo full revalidation | Partial. `service_plan` checks connecting time, route, locks, terminal capabilities and compliance, and `reserve_plan` checks resources. Receiver opening windows, variable handling throughput, cutoff and service commitment policy are absent. |
| D3: expired/materially changed quotes require acceptance | Missing/failing. Booking accepts `approved: true` and recomputes terms, without a quote version or expiry. |
| D3: a new rate card cannot silently alter accepted terms | Missing/failing. Versioned terminal cards do not exist; changing a vessel tariff increased a confirmed booking price without fresh acceptance. |
| D3: invoice equals accepted terms plus authorized amendments | Partial. The invoice matches the newly computed booking, but there is no accepted quote binding or amendment approval history. |
| D3: tenant approval and commercial privacy | Existing foundation passes the current access/redaction tests. Cargo ownership is checked for every pooled member; no new per-customer quote acceptance workflow exists. |
| D4: four trips have four valid assignments | Missing. The road booking has one unassigned route leg and no per-trip resource jobs. |
| D4: missing/declined jobs block bundle confirmation | Missing. Provider acceptance/decline/expiry records and bundle confirmation do not exist. |
| D4: operator accepts the reviewed departure plan version | Missing. Availability posting is supported, but no separate departure acceptance bound to load/contribution/terms exists. |
| D4: repeated submission creates no duplicate booking | Working rejection guard. The duplicate-booking and simultaneous-booking tests passed; repeated submission returns a conflict rather than another booking. |
| D4: 12 t indivisible piece fails a 10 t lift limit | Missing. No indivisible-piece field exists; the current demo threshold is capped at 10 t. |
| D4: simulated events/tracking are labeled | Working for existing demo tracking and transcript fallback. The required simulated provider-job workflow itself is absent. |

The additional D4 service-owner organization, named dispatcher, intervention queue and next-action ownership are not persisted as a complete delivery ownership workflow. Existing role workspaces and operational records are reusable foundations.

The following findings were reproduced with actual application services and HTTP endpoints against fresh seeded, foreign-key-enabled in-memory SQLite databases. No running demo database was reset or modified.

1. **High priority: a pooled booking can accept cargo that misses its final delivery deadline.**

   In [bookings.py](../backend/services/bookings.py), lines 257–263 copy the combined plan's `eta` to every member. The combined cargo uses the anchor's final delivery location, so another member's last road leg is omitted from its saved ETA and deadline check.

   Reproduction: keep the seeded 80 t anchor; set `pool-cargo.last_mile_required = True`, its destination coordinates to `[9.498, 76.428]`, and its deadline to readiness plus 9 h 20 min. Optimize and approve the common-terminal pool on `vembanad`. Both bookings are accepted with ETA **17:09 IST on 8 October**. The second cargo's retained 13.32 km final road leg makes its modeled arrival approximately **17:34 IST**, after its **17:20 IST** deadline. About 25 minutes of travel disappear from its saved ETA.

   Required change: synchronize common loading/sailing/unloading intervals, then compute and revalidate each member's pickup and final delivery separately. Recalculate waiting charges and duration fields from the final intervals.

2. **High priority: cancellation removes shared scheduled-service berths while another load remains confirmed.**

   [terminal_resources.py](../backend/services/terminal_resources.py), lines 81–88, preserves inactive owners' resources only when an active `pool_id` member exists. Lines 232–246 share scheduled-service berth/equipment reservations by skipping duplicate records, but those records still belong to the first booking. Scheduled bookings have no pool identifier.

   Reproduction: set both seeded outbound loads to 40 t, origin Maradu, and no first-mile requirement. Book both separately on `periyar` / `nw3-service`; cancel the first shipment through the dispatch transition endpoint. The second remains **CONFIRMED**, but calendar berth reservations drop from **2 to 0**; total visible resource reservations drop from **10 to 4**. The remaining four are storage and its separately required crane reservations.

   Required change: attach common allocations to the departure/voyage lifecycle and retain every resource needed by the remaining commitments. Regression coverage must include scheduled members as well as explicit pools.

   The specific first-member cancellation issue described in agent.md is **partly addressed already**: on the ordinary seeded 138 t pool, all **8 resource reservations remain** after its first member cancels. Do not describe that normal resource path as entirely unfixed. The older TerminalSlot fallback still filters only by its owning booking's active status in [checks.py](../feasibility/terminal_constraints/checks.py).

3. **High priority: booking can silently accept a different price from the displayed quote.**

   [BookingCreate](../backend/schemas/requests.py) has `approved` but no quote version identifier. [bookings.py](../backend/services/bookings.py), lines 179–192, recomputes mode quotes during booking. [Planner.tsx](../frontend/src/components/Planner.tsx), lines 72–82, sends `approved: true` without an accepted amount or version.

   Reproduction: display the seeded hero HYBRID quote at **₹35,391.34**; increase the vessel's stored per-tonne-km rate by 1; submit the same booking request. The API returns a **CONFIRMED** booking at **₹40,511.34**, a **₹5,120** increase, without requesting fresh acceptance. This case changes the local tariff record directly; no real provider was contacted.

   Required change: persist the complete expiring quote version and bind approval to it. Handle material changes by returning a new quote for explicit acceptance. Retain the existing booking snapshot and invoice tracing as a foundation.

4. **High priority: an 80 t road booking confirms without four truck assignments.**

   [costs.py](../optimization/multimodal/costs.py), lines 46–50, prices weight × distance; [bookings.py](../backend/services/bookings.py), lines 327–347, creates one route leg for an entire road booking and leaves its provider unset.

   Reproduction: approve the seeded 80 t hero with mode ROAD. It becomes **CONFIRMED** with **one ShipmentLeg**, `assigned_provider = None`, and no truck-job acceptance bundle. A route leg can legitimately contain several trucks, but those four required 20 t truck assignments do not exist in this implementation.

   Required change: model trips separately from route legs, price the configured tariff semantics and create resource/time assignments for every trip. Confirm the simulated bundle only after all required providers accept.

   Cargo input also has no heaviest indivisible-piece field. [terminal checks](../feasibility/terminal_constraints/checks.py), lines 51–62, use `min(total_weight, 10)` as a demo crane threshold, so the required 12 t piece versus 10 t lift acceptance case cannot be represented correctly yet. Handling uses a universal 0.75 h duration.

5. **High priority: one member's transition can mark an active voyage's vessel available.**

   [bookings.py](../backend/services/bookings.py), lines 555–561, derives `vessel.state` only from the current shipment transition.

   Reproduction: approve the 138 t pool, advance the second shipment to IN_TRANSIT, and cancel the still-CONFIRMED first shipment. The second remains **IN_TRANSIT**, but the vessel changes from **SAILING to AVAILABLE**. Overlapping-booking checks still provide a separate capacity guard; this finding establishes incorrect operational state, not a reproduced vessel double booking.

   Required change: derive vessel state from the voyage and all relevant active commitments; define which member transitions are permitted once the shared departure has begun.

6. **Medium priority: utilization remains stale after cancellation.**

   [impact.py](../backend/services/impact.py), lines 152–154, averages saved booking-time utilization. The stored PoolingGroup totals are also unchanged by [transition](../backend/services/bookings.py).

   Reproduction: after cancelling the 80 t member, active water tonnes correctly become **58**, but reported utilization remains **92%** and stored pool tonnage remains **138**. Remaining modeled occupancy is **58 / 150 = 38.7%**. This mismatch affects the required cancellation viability review; actual sailing contribution cannot be recomputed because D1's contribution model is absent.

   Required change: calculate current voyage tonnes, volume, utilization and contribution from active commitments, and label original projections separately where they are retained.

7. **Medium priority: a cancelled return booking still counts as a backhaul benefit.**

   [bookings.py](../backend/services/bookings.py), line 481, sets the earlier outbound metric's `empty_return_avoided` flag when a return is booked. Cancellation does not clear or recompute that link. [impact.py](../backend/services/impact.py), line 157, continues counting the outbound flag.

   Reproduction: approve the seeded outbound pool, book the 62 t return on the same vessel, then cancel that return through the dispatch endpoint. `backhaul_matches` remains **1**, despite the return booking being **CANCELLED**.

   Required change: derive the benefit from an explicit active return-booking link and distinguish proposed, committed and completed returns. Clear or recompute the benefit when either leg is cancelled or replanned.

   Performance metrics also need careful scope: `calculate_impact` still uses planned departure/ETA for its explicitly labeled estimated reliability values. The separate corridor analytics service uses recorded milestones. The guide's actual-timestamp rule must be applied consistently before claiming observed delivery performance.

The guide itself is a strong direction: it gives concrete acceptance cases, keeps deterministic checks authoritative, distinguishes simulated commitments from real confirmations, and separates demo work from pilot integrations. Two alignment issues remain: its first-member cancellation observation needs the qualification above, and [the presentation outline](PRESENTATION_OUTLINE.md) does not yet contain the promised D1-only / D1+D2 fallback tiers or `success-metrics` section. The older feature audit addresses older prototype scope and should not be treated as proof of D1–D4 completion.

Fresh verification performed:

- `.venv/Scripts/python.exe -m pytest -p no:cacheprovider`: **93 passed**, one third-party Starlette/httpx deprecation warning, **23.93 s** in this fresh run.
- `npm run build` in `frontend`: **passed** TypeScript and Vite production compilation. The initial sandbox run hit esbuild `spawn EPERM`; the authorized retry outside the sandbox passed.
- `.venv/Scripts/python.exe .runtime/x1/review_agent_alignment.py`: **six disposable scenarios completed and reproduced all seven findings**, including the retained normal-pool resources and cancelled-return metric. Current-defect assertions are diagnostic evidence, not passing target acceptance tests. The script and raw JSON results are retained under ignored `.runtime/x1/review_agent_alignment.py` and `.runtime/x1/review_agent_alignment.json`.
- `.venv/Scripts/python.exe scripts/check_repository.py`: **passed**, checking **800 local documentation links and 190 publication files with zero findings** in the final run. The checker validates local file paths, not Markdown section anchors. The existing ignore policy, including ignored `agent.md`, was preserved.
- Browser end-to-end tests and credentialed external-provider checks were **not run** in this review. Historical browser results are not claimed as fresh evidence.

Proceed with the guide's D1 → D2 → D3 → D4 order, adding focused acceptance regressions for the reproduced cases. Preserve the current authorization, duplicate-booking, transactional rollback and physical feasibility checks. Update capability claims and presentation tiers only as each gate passes.

Application source was not changed during this review. This report was updated and ignored isolated reproduction artifacts were added; `agent.md` and the existing `.gitignore` were preserved. No external bookings, messages, payments, publication or credentialed provider calls were made.
