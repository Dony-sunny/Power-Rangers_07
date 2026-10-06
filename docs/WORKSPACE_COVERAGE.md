# Role workspace coverage

One shared database backs all roles. This matrix distinguishes working prototype tasks from advanced architecture/roadmap rather than implying every peripheral production feature is connected.

| Role | Implemented workspace/action | Architecture / roadmap |
|---|---|---|
| Shipper procurement | Manual/text/PDF intake, review, CSV preview, candidate quotes, door-to-door modes, cost/carbon/SLA, approved individual/pooled/scheduled bookings and request history | CargoPreference stores preferred-operator/ranking/recurring-contract configuration; negotiated contracts, external rate-history feeds and actual recurring invoicing are not connected |
| Shipper dispatch | Timeline, route positions/ETA, valid state progression, replacement/road recovery with approval, prototype manifests/instructions | ShipmentLeg assigned_provider and operational truck_assignment support first/last-mile assignment; carrier API, automated truck appointment and rescheduling UX remain extensions |
| Warehouse | Booked loads, actual weight guard, volume verification, packing/handover persistence, loading sheet | Labels/QR, damage-photo storage, detailed packing/loading sequence and gate scanner are extensions |
| Consignee | Incoming cargo/ETA, quantity received, receipt name, damage/discrepancy note, delivery/POD package | Verified OTP/digital signature and photo evidence service are extensions |
| Vessel commercial operator | Own capacity/booked load, calculated compatible demand, pool projection, potential freight, backhaul, synthetic reliability/certificates; voice availability | Contract negotiation, operator settlement subscription analytics and production demand/rate feeds |
| Fleet dispatcher | Own vessel profiles, manual registration, voice/manual availability, operational states and assigned shipments | Crew records, whole-fleet VRP/repositioning and advanced service participation |
| Captain | Responsive assigned voyages, manifest, approved-route snapshot, ETA/instructions, departure/arrival milestones, unverified reports; financial fields redacted | GPS integration, weather/official notices, fully disconnected synchronization |
| Terminal operator | Berth calendar/reservation windows, vessel/cargo arrival records, equipment/storage/operational status and handling charges | Multi-berth/equipment crews, storage bookings, actual truck/gate appointments and delay negotiation |
| 3PL control tower | Distinct active/delivered/intervention board, shipment timeline/recovery, trusted cross-tenant planning, pooling and scheduled services | Bulk allocation/contract-specific SLA analytics, external carrier feeds and advanced fleet optimizer |
| Finance | Generated itemized invoice/payment records, pending/paid/disputed/settled transitions, delivery-gated payout and prototype invoice | Real payment/escrow/insurance provider and tax/regulatory integration |
| Compliance | Registration/insurance/dangerous-goods register, expiry review, verified demo certificate recording, audit and deterministic booking gate | Real legal validation, document authenticity and authority workflow integration |
| Maintenance | Defect note, downtime/booking block, inspection/due date and return-to-service | Predictive maintenance and IoT defect feeds |
| Waterway control | Map/segment restrictions and provenance, terminal capabilities, unmet demand, navigation reports with expiry; demo closures | Live hydrographic/lock status, official notice ingestion and authority verification workflows |
| Government | Booking-derived selected/completed impact, demand map/chart, backhaul, unserved requests, gap/activation decision support and modal-shift evaluation | Validated network histories, audited public reporting and authoritative infrastructure planning |
| Admin/trust | Organization and user/role models/register, audit, provider/demo status, reset and six deterministic scenarios | Full identity onboarding/custom role management, disputes workflow and production admin policy console |

No real WhatsApp, payment, government, GPS, weather or insurance connector is fabricated. JSON document packages are prototype ready-data exports. The intentionally broad ecosystem has a complete core vertical slice and P1 workflow, with peripheral feature boundaries documented.
