# Security review

Reviewed 7 October 2026 for the local hackathon prototype.

## Implemented controls

- Secrets are read from environment / ignored `.env`. `.env.example` has empty credential values. Provider errors expose generic status, never API keys or response bodies.
- Pydantic rejects unknown request fields, nonfinite/negative capacities, unbounded text, invalid location coordinates and unordered/non-timezone-aware cargo/availability windows.
- Demo identities resolve stored users/roles. Every write checks role permission and ownership; scoped reads hide absent/foreign records with 404. Captains receive no quote totals, rate or nested commercial snapshot. Warehouse cannot read government metrics. Shippers cannot read or approve competitor requests/pools.
- DEMO_MODE=false disables role-header identity and synthetic controls. Signed bearer payloads require a strong HMAC key, stored subject and expiry. There is no public token minting endpoint.
- Uploads are capped at 8 MB, types restricted, filenames stripped to basenames, PDF/image signatures checked. Text PDFs must be unencrypted and at most 40 pages. Documents are not executed, unpacked or saved under user-controlled filesystem paths. Scanned PDFs cannot silently create invented fields.
- Model content is treated as data. Schema validation and bounded tool allowlists prevent arbitrary code, SQL, path access or safety overrides. Broker planning cannot automatically approve bookings.
- Booking approval and recovery approval are explicit. SQLite capacity checks/writes are serialized; duplicate bookings and service overcapacity are rejected. Invalid shipment transitions are rejected.
- CORS defaults to the two localhost frontend origins. Responses have `nosniff` and `no-store`. Generic unexpected errors avoid secret leakage. Local services bind to 127.0.0.1.
- Structured audits record entity/event/actor and safe details; uploaded document text and credentials are not logged.
- XLSX validates decompressed size, sheet/row/column limits and rejects formulas, macros/external links and duplicate mapped headers. Valid-only import is scoped, expiring, explicitly approved and protected from reuse; all rows commit together. Error-report cells are sanitized against spreadsheet formula injection.
- OCR/text PDF processing runs fixed application modules in subprocesses with timeouts; byte/page/pixel limits are enforced. Canonical private JPEG evidence strips EXIF. Photo access, QR creation/resolve and OTP issuance enforce assigned-record scope. Opaque QR IDs are 128-bit random references and confer no access.
- OTP stores a salted scrypt hash, five-minute expiry, receiver identity, five-attempt limit, issuance cooldown/rate cap and single-use completion. Local code is returned only in demo mode; no reusable code is retained in plaintext. Once requested, verification gates delivery; preserved milestone-only demo delivery is explicitly unverified.
- Admin role changes use stored roles, disabled users lose access, and the active admin cannot disable/demote itself. Browser role switching is visible only in demo mode. Capacity holds, fleet approvals, terminal resources and whole-pool recovery revalidate within transactions.

## Verification

Integration tests exercise tenant boundaries, captain commercial redaction, restricted analytics, false file signatures/executable uploads/oversize files, missing approval, duplicate booking, invalid state skips and non-demo identity rejection. Dependency audit reported no npm vulnerabilities during installation. No internet provider was credential-tested.

## Production gaps

Demo role switching is intentionally not authentication. Do not publish a demo-mode instance with sensitive data. Real deployment needs a managed identity provider, identity provisioning/revocation, HTTPS, per-organization policy administration, rate limiting, CSRF considerations where cookie identity is added, storage encryption/retention/deletion, file malware/OCR isolation and PDF resource-limits in a separate worker. A page-count/byte limit is not a full PDF decompression-bomb defense. The bearer abstraction is a prototype gateway boundary, not full SSO.

Real navigation, dangerous-goods certification and compliance cannot be established by seeded records or an LLM. Registered-vessel evidence and official operational sources must be validated before deployment. Payment states do not move real money. Data packages do not issue official tax/regulatory documents.

## Production identity provider boundary

`IdentityProvider.verify_token` in `backend/services/connectors.py` is the future OIDC/OAuth2/enterprise SSO verification contract. A production adapter must verify issuer/audience/signature/expiry against trusted keys, reject replay where applicable, map immutable subjects to stored users and recheck disabled status/stored roles on every request. A client role header/claim must never grant authority. Provisioning, key rotation, logout/revocation, tenant invitations and audit retention need a managed identity deployment and tests; no public token-minting endpoint or fake SSO was added.

Photos in database JSON/text are prototype storage. Production requires private object storage, encryption, signed authorized retrieval, retention/deletion, upload quotas and malware/resource-isolated processing. Cross-worker PostgreSQL locking is an explicit migration requirement. See [Migration](POSTGRESQL_MIGRATION.md) and [Publication review](GITHUB_PUBLICATION.md).
