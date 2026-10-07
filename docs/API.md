# API

Base: `http://127.0.0.1:8000/api`. OpenAPI and exact request/response schemas: `/docs` and `/openapi.json`. Errors use 401/403 for identity/permissions, 404 for hidden or absent records, 409 for constraints/workflow conflicts, 413 for size limits, 415 for unsupported files and 422 for schema/review failures.

In demo mode send `X-Demo-Role: shipper` (default), operator, dispatch, warehouse, receiver, fleet, captain, terminal, control, finance, compliance, maintenance, network, government or admin. Optional `X-Demo-User` selects a stored matching-role identity; `competitor-user` demonstrates tenant isolation. These headers are ignored outside demo mode.

| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | Provider/demo status and role catalog |
| GET | `/workspace` | Actor-scoped role data, redacted financial fields |
| POST / GET | `/cargo` | Create / list scoped cargo |
| POST | `/cargo/{id}/documents/{document_id}` | Attach an intake document belonging to the actor |
| POST | `/vessels` | Register own vessel; compliance initially PENDING |
| POST | `/availability` | Confirm own vessel's window, capacity and corridor |
| GET | `/cargo/{id}/matches?profile=BALANCED` | Persist candidate evidence/quotes; reject unsafe candidates |
| GET | `/cargo/{id}/compare?vessel_id=vembanad` | Road/water/hybrid plans and source assumptions |
| POST | `/cargo/{id}/pool?vessel_id=vembanad` | OR-Tools preview; scoped eligible loads |
| POST | `/cargo/{id}/backhaul?vessel_id=vembanad` | Validated reverse-load proposals |
| GET | `/vessels/{id}/opportunities` | Own operator's compatible demand, pool and return preview |
| GET | `/services` | Stops, segment usage, remaining scheduled capacity; trusted-role proposals |
| POST | `/bookings` | Approved cargo/vessel/mode, optional pool_id/service_id; atomic reservation and shipment |
| GET | `/shipments/{id}` | Scoped milestones, legs and simulated position |
| POST | `/shipments/{id}/transition` | Allowed next state; invalid skip returns 409 |
| POST | `/shipments/{id}/operations` | Role-scoped weight/volume, packing, truck, handover or receipt data |
| POST | `/bookings/{id}/disrupt` | Eight demo pre-departure types; includes equipment/not-ready/late-truck/service cancellation/reduced capacity |
| GET | `/bookings/{id}/recovery` | Current revalidated alternatives; no rebooking |
| POST | `/bookings/{id}/recover` | Explicitly approved replacement/fallback |
| GET | `/bookings/{id}/documents/{kind}` | Prototype JSON package; commercial kinds restricted |
| GET | `/impact` | Government/control/network/admin booking-derived metrics |
| GET | `/intelligence/modal-shift` | Trusted-role deterministic modal suitability |
| POST | `/reports` | Unverified navigation report with expiry |
| POST | `/vessels/{id}/maintenance` | Own maintenance/defect/return-to-service |
| POST | `/vessels/{id}/certificates` | Compliance/admin recorded verification and expiry |
| POST | `/payments/{id}/status` | Finance-only simulated payment/dispute/settlement state |
| POST | `/intake/cargo/text` | Structured nullable cargo extraction; no persistence |
| POST | `/intake/cargo/document` | Multipart PDF/TXT/CSV/PNG/JPEG; document/extraction stored, no cargo yet |
| POST | `/intake/cargo/bulk-preview` | CSV/XLSX per-row validation and scoped expiring preview; no cargo insertion |
| POST | `/intake/vessel/text` | Malayalam/transliterated transcript extraction |
| POST | `/intake/vessel/audio` | Multipart audio, optional explicit `use_demo_transcript=true` |
| POST | `/intake/vessel/demo` | Demo-only disclosed sample transcript |
| POST | `/broker` | `{text,cargo_id?}` bounded planning tools or intake review |
| POST | `/demo/reset` | Admin/demo-only clear transactions and reseed |
| POST | `/demo/scenario` | Admin/demo-only `{scenario:"A".."F"}` |

Cargo timestamps require timezone offsets and an ordered window. Nonfinite/negative weights are invalid. Availability cannot exceed the registered vessel. Booking requires `approved:true` and revalidates data under a SQLite write lock. The same cargo cannot be booked twice or exceed a scheduled service segment limit. Pooling requires confirmed volumes.

Example booking:

```json
{"cargo_id":"hero-cargo","vessel_id":"vembanad","mode":"HYBRID","approved":true}
```

Document kinds: confirmation, manifest, loading-sheet, transport-instruction, delivery-note, invoice and proof-of-delivery. The output is a prototype data package, not an official statutory document or e-way bill.

## Continuation endpoints

| Method | Path | Behavior |
|---|---|---|
| GET / POST | `/providers/diagnostics` | Admin configuration/state and read-only validated LLM probe; no secrets |
| GET | `/providers/tracking/{vessel_id}`, `/providers/weather` | Authorized validated optional provider reads with disclosed simulated fallback |
| GET | `/intake/cargo/bulk-template` | XLSX template |
| GET | `/intake/cargo/bulk-preview/{id}/errors` | Scoped sanitized CSV error report |
| POST | `/intake/cargo/bulk-import/{id}?approved=true` | Atomic valid-only import; expiry/reuse/ownership guard |
| GET / POST | `/service-patterns` | Dated recurring patterns and occurrences / generate within 90 days |
| POST | `/services/recurring-bookings` | Up to 12 approved date reservations, all or none |
| POST | `/services/{id}/cancel` | Cancel one occurrence; preserve pattern and replan affected bookings |
| POST | `/capacity-contracts` | Hold per-departure segment capacity and agreed freight rate |
| GET / POST | `/terminals/resources` | Scoped calendar / create resource |
| POST | `/terminals/reservations` | Collision-checked manual interval reservation with alternate suggestion |
| POST | `/terminals/truck-appointments` | Assigned shipment gate reservation and truck assignment |
| GET | `/fleet/demand` | Operations-only demand summary with private commercial fields omitted |
| POST | `/fleet/optimize` | Bounded CP-SAT preview; configurable objective and explanations |
| POST | `/fleet/plans/{id}/approve?approved=true` | Control/admin atomic revalidation and bookings |
| POST | `/bookings/{id}/recover-pool` | Explicitly approved combined pool recovery |
| POST / GET | `/shipments/{id}/photos` | Private canonical photo upload / metadata |
| GET | `/photos/{id}` | Authorized private evidence content |
| GET | `/labels/{kind}/{id}`, `/labels/{kind}/{id}/print` | Opaque QR and printable label for cargo/booking/shipment |
| GET | `/labels/{reference}` | Resolve opaque QR under actor authorization |
| POST | `/shipments/{id}/delivery-challenge` | Receiver local demo OTP at unloading/last mile |
| POST | `/delivery-challenges/{id}/verify` | Expiry/receiver/attempt/single-use verification |
| POST | `/admin/organizations`, `/admin/users` | Admin creates organization/member |
| PATCH | `/admin/users/{id}` | Stored role change or disable |
| GET | `/intelligence/corridors`, `/intelligence/failed-demand` | Actual milestone samples / typed unique demand attribution |
| POST | `/intelligence/modal-shift/upload` | Historical CSV/XLSX potential opportunity classification |
| GET / POST | `/cargo/{id}/rate-benchmark`, `/cargo/{id}/reject-quote` | Comparable sample range / explicit price rejection |
| PATCH | `/reports/{id}` | Network/admin review and explicit conservative restriction promotion |
| POST / GET | `/reports/{id}/photos` | Navigation observation photos |
| GET | `/payments/{id}/history` | Authorized prototype payment audit history |
| POST | `/demo/judge/step` | Admin/demo-only guided checkpoint, explicit approvals and persisted evidence |

Exact schemas and access checks remain in OpenAPI and the source modules; this index is descriptive. All prototype/no-op boundaries are detailed in [Known limitations](KNOWN_LIMITATIONS.md).
