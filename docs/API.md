# Restored team API boundaries

All endpoints retain demo-identity or signed-bearer authentication. UI grouping does not grant backend permissions.

| Endpoint | Behavior |
| --- | --- |
| `GET /api/workspace` | Scoped existing operations snapshot. Shipment booking rows include `voyage_id` to distinguish shared delivery from legacy individual workflows. Commercial fields are withheld from operational staff. |
| `GET /api/lines` | Returns `departures`, impact for the entrusted coordinator, and simulated tariff provenance. All existing team identities can read only authorized voyages. Seller teams see only their organization's consignments. Each departure exposes `allowed_milestones`, `can_receive` and per-member `delivery_verification` flags. |
| `GET/POST /api/lines/cargo/{id}/profile` | Read/review load-piece requirements. Only cargo writers may save; accepted load profiles are locked. Imported loads require reviewed units before a dated quote. |
| `POST /api/shipments/{id}/operations` | Existing role-owned handover/crew/handling metadata. A shared booking's accepted volume, mass and truck assignment cannot be amended here. Receiver quantities cannot exceed the consignment and must be recorded after unloading. |
| `POST /api/lines/{id}/milestone` | Ordered common voyage milestones. Scoped coordinator, own operator/fleet/captain, eligible seller dispatch or assigned terminal operations only. |
| `POST /api/lines/{id}/receipt` | Own receiver or scoped coordinator records an individual receipt after unloading. A requested receiver challenge must be verified before completion. Records actor, quantity, timestamp and simulated source. |
| `POST /api/shipments/{id}/delivery-challenge` | Existing local receiver challenge; no SMS is sent. |
| `POST /api/delivery-challenges/{id}/verify` | Existing identity-bound, expiring, single-use local verification. |
| `GET /api/corridor-context` | Authenticated sourced IWAI reference and fixed weather-location choices. |
| `GET /api/corridor-context/weather?location=maradu` | Read-only Open-Meteo model with validated timestamps, units and explicit cached/unavailable state. Other supported keys: `vaikom`, `thanneermukkom`, `alappuzha`. Arbitrary URLs are rejected. |

Existing legacy optimization, recurring services, appointments, documents, photos, QR labels, maintenance, finance and administration APIs remain available through their corresponding restored screens. Legacy transitions and recovery controls are hidden for shared bookings; these use voyage-level actions instead.
