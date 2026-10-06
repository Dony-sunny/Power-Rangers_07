from sqlalchemy import select
from backend.config import settings
from backend.models import VesselCertificate, VesselMaintenanceStatus
from backend.services.timeutils import dt


def compliance_checks(db, cargo, vessel, departure, arrival=None):
    reasons = []
    through = arrival or departure
    if vessel.compliance_status != "PASS":
        reasons.append("Vessel/operator compliance status is not PASS.")
    if settings.enforce_certificates:
        certificates = list(
            db.scalars(
                select(VesselCertificate).where(
                    VesselCertificate.vessel_id == vessel.id
                )
            )
        )
        required = ["REGISTRATION", "INSURANCE"] + (
            ["DANGEROUS_GOODS"] if cargo.hazardous else []
        )
        for kind in required:
            valid = any(
                c.kind == kind and c.verified and dt(c.expires_at) > through
                for c in certificates
            )
            if not valid:
                reasons.append(
                    f"{kind}: verified certificate missing or expires before voyage completion."
                )
    status = db.scalar(
        select(VesselMaintenanceStatus).where(
            VesselMaintenanceStatus.vessel_id == vessel.id
        )
    )
    if status and status.status != "OPERATIONAL":
        reasons.append("Maintenance inspection record blocks booking.")
    if status and status.due_date and through.date().isoformat() > status.due_date:
        reasons.append(
            "Maintenance inspection becomes overdue before voyage completion."
        )
    return reasons
