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
| POST | `/bookings/{id}/disrupt` | Demo pre-departure VESSEL_UNAVAILABLE / ROUTE_CLOSED / TERMINAL_CLOSED |
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
| POST | `/intake/cargo/bulk-preview` | CSV schema validation; rows saved only after confirmation |
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
