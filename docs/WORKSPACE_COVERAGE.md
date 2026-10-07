# Operational workspaces

The marketplace retains three main workspaces. **Team tools** reconnects the existing specialist screens using their original scoped identities and permissions. Switching a team role is available only in demo mode. A signed production identity can use only its stored role.

| Main workspace | Team identities | Tools |
| --- | --- | --- |
| Cargo owner / seller | Shipper procurement, shipper dispatch, warehouse, consignee, seller finance | Text/document/OCR/CSV/XLSX intake, reviewed load units, matching, pooling, backhaul, recurring capacity, tracking, truck appointments, packing/gate-out records, photos, QR labels, receiver verification, receipts, invoice drafts and simulated settlements |
| Boat operator | Vessel operator, fleet dispatcher, captain, maintenance | Dated services, corridor history, navigation observations, fleet optimization, crew assignment, approved routes, common voyage milestones, defects and inspections |
| Logistics coordinator | Coordinator, terminal operator, compliance/safety, waterway control, government analytics, platform admin | Entrusted cargo coordination, shared resources, terminal handling, evidence, certificate review, reports, operational intelligence, stored user management, provider diagnostics and demo controls |

The government component is retained as an integration point for the teammate's analysis work. Its calculations and layout were not changed in this restoration.

Vembanad and Pamba operator accounts have separate operator/fleet/captain/maintenance demo identities. Account selection carries through API calls and downloads. A team identity cannot approve a commercial quote by inheriting its parent's UI group.

Shared deliveries use one voyage workflow. Operator/fleet/captain can advance their own vessel's common milestones. A terminal may record only its assigned loading/unloading operations. Seller dispatch can advance a shared departure only when all active consignments belong to its organization. Warehouse verification does not amend accepted dimensions, mass, resource assignments or charges. Receivers see and complete only their organization's consignments; an active requested verification challenge must pass first.

Every team also has read-only [public corridor context](DATA_PROVENANCE.md). This context does not provide navigation clearance or override deterministic feasibility.
