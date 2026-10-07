import base64
import hashlib
import hmac
import secrets
from datetime import timedelta
from io import BytesIO
from uuid import uuid4
from html import escape
import qrcode
import qrcode.image.svg
from fastapi import HTTPException
from sqlalchemy import select
from backend.models import *
from backend.repositories.common import uid, require, record, audit
from backend.services.bookings import booking_access
from backend.services.timeutils import utcnow, dt
from backend.config import settings
from intelligence.document_intake.ocr import validate_image


def shipment_access(db, actor, shipment_id):
    shipment = require(db, Shipment, shipment_id)
    booking = require(db, Booking, shipment.booking_id)
    booking_access(db, actor, booking)
    return shipment, booking


def save_photo(db, actor, shipment_id, content, category, description):
    shipment_access(db, actor, shipment_id)
    roles = {
        "warehouse",
        "dispatch",
        "receiver",
        "terminal",
        "admin",
        "control",
        "captain",
    }
    if actor.role_id not in roles:
        raise HTTPException(
            403, "Photo evidence requires an assigned operational role."
        )
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, "Evidence image limit: 2 MB.")
    if (
        category
        not in {
            "LOADING",
            "HANDOVER",
            "DAMAGE",
            "TERMINAL",
            "DISCREPANCY",
            "POD",
            "NAVIGATION",
        }
        or len(description) > 1000
    ):
        raise HTTPException(
            422, "Choose a supported evidence category and a short description."
        )
    if (
        len(
            list(
                db.scalars(
                    select(EvidencePhoto).where(
                        EvidencePhoto.shipment_id == shipment_id
                    )
                )
            )
        )
        >= 20
    ):
        raise HTTPException(413, "Evidence limit: 20 photos per shipment.")
    image = validate_image(content)
    image.thumbnail((1600, 1600))
    output = BytesIO()
    image.save(output, "JPEG", quality=85)
    photo = EvidencePhoto(
        id=uid("photo"),
        shipment_id=shipment_id,
        uploader_id=actor.id,
        category=category,
        description=description,
        image_base64=base64.b64encode(output.getvalue()).decode(),
        mime_type="image/jpeg",
    )
    db.add(photo)
    audit(
        db,
        "evidence.photo_saved",
        photo.id,
        actor,
        shipment_id=shipment_id,
        category=category,
    )
    db.commit()
    return photo_metadata(photo)


def photo_metadata(photo):
    return {key: value for key, value in record(photo).items() if key != "image_base64"}


def label_entity(db, actor, kind, entity_id):
    if kind == "shipment":
        shipment, booking = shipment_access(db, actor, entity_id)
        cargo = require(db, CargoRequest, booking.cargo_id)
        shipment_id = shipment.id
    elif kind == "booking":
        booking = require(db, Booking, entity_id)
        booking_access(db, actor, booking)
        cargo = require(db, CargoRequest, booking.cargo_id)
        shipment = db.scalar(select(Shipment).where(Shipment.booking_id == booking.id))
        shipment_id = shipment.id if shipment else None
    elif kind == "cargo":
        from backend.auth import cargo_access

        cargo = require(db, CargoRequest, entity_id)
        try:
            cargo_access(actor, cargo)
        except HTTPException:
            booking = db.scalar(select(Booking).where(Booking.cargo_id == cargo.id))
            if not booking:
                raise HTTPException(404, "Record not found.") from None
            booking_access(db, actor, booking)
        shipment_id = None
    else:
        raise HTTPException(422, "Labels support cargo, booking or shipment.")
    return {
        "kind": kind,
        "id": entity_id,
        "shipment_id": shipment_id,
        "cargo_type": cargo.cargo_type,
        "weight_tonnes": cargo.weight_tonnes,
        "origin": cargo.origin,
        "destination": cargo.destination,
    }


def make_label(db, actor, kind, entity_id):
    entity = label_entity(db, actor, kind, entity_id)
    reference = db.scalar(
        select(LabelReference).where(
            LabelReference.entity_type == kind, LabelReference.entity_id == entity_id
        )
    )
    if not reference:
        reference = LabelReference(
            id="label-" + uuid4().hex, entity_type=kind, entity_id=entity_id
        )
        db.add(reference)
        db.commit()
    payload = f"/#/record/{reference.id}"
    qr = qrcode.make(payload, image_factory=qrcode.image.svg.SvgPathImage)
    output = BytesIO()
    qr.save(output)
    return {
        "reference": reference.id,
        "payload": payload,
        "qr_svg": output.getvalue().decode(),
        "entity": entity,
        "authorization_required": True,
    }


def printable_label(label):
    entity = label["entity"]
    return (
        '<!doctype html><html><head><meta charset="utf-8"><title>Jalayatra cargo label</title><style>body{font:18px system-ui;padding:32px}svg{width:240px;height:240px}small{display:block;margin-top:16px}</style></head><body><h1>Jalayatra AI</h1><h2>'
        + escape(entity["id"])
        + "</h2><p>"
        + escape(entity["cargo_type"])
        + " · "
        + str(entity["weight_tonnes"])
        + " t</p><p>"
        + escape(entity["origin"])
        + " → "
        + escape(entity["destination"])
        + "</p>"
        + label["qr_svg"]
        + "<small>Opaque reference: "
        + escape(label["reference"])
        + " · Sign in to open the authorized record inside Jalayatra.</small></body></html>"
    )


class LocalDemoOTPProvider:
    name = "local_demo_otp"

    def issue(self):
        if not settings.demo_mode:
            raise HTTPException(
                503,
                "Local OTP is demo-only. Configure an authenticated SMS/email provider for production.",
            )
        return f"{secrets.randbelow(1_000_000):06d}"


def request_challenge(db, actor, shipment_id):
    shipment, booking = shipment_access(db, actor, shipment_id)
    if actor.role_id not in {"receiver", "admin"}:
        raise HTTPException(403, "Delivery challenge requires receiver identity.")
    if shipment.status not in {"UNLOADING", "LAST_MILE"}:
        raise HTTPException(409, "Request delivery verification at the delivery stage.")
    now = utcnow()
    recent = [
        item
        for item in db.scalars(
            select(DeliveryChallenge).where(
                DeliveryChallenge.shipment_id == shipment_id
            )
        )
        if dt(item.created_at) > now - timedelta(minutes=15)
    ]
    if len(recent) >= 3:
        raise HTTPException(
            429, "Delivery challenge limit: three requests in fifteen minutes."
        )
    if any(dt(item.created_at) > now - timedelta(seconds=30) for item in recent):
        raise HTTPException(
            429, "Wait thirty seconds before issuing another challenge."
        )
    code = LocalDemoOTPProvider().issue()
    salt = secrets.token_hex(32)
    for item in recent:
        if not item.verified_at:
            item.expires_at = now.isoformat()
    challenge = DeliveryChallenge(
        id=uid("pod"),
        shipment_id=shipment_id,
        receiver_id=actor.id,
        salt=salt,
        otp_hash=hashlib.scrypt(
            code.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
        ).hex(),
        expires_at=(now + timedelta(minutes=5)).isoformat(),
        verified_at=None,
    )
    db.add(challenge)
    shipment.operational_data = {
        **shipment.operational_data,
        "pod_required": True,
        "pod_verified": False,
    }
    audit(
        db, "delivery.challenge_created", challenge.id, actor, shipment_id=shipment_id
    )
    db.commit()
    return {
        "challenge_id": challenge.id,
        "expires_at": challenge.expires_at,
        "demo_otp": code,
        "provider": "Local demo OTP · no SMS sent",
        "signature_status": "Prototype verification, not a legal digital signature",
    }


def verify_challenge(db, actor, challenge_id, code):
    challenge = require(db, DeliveryChallenge, challenge_id)
    shipment, booking = shipment_access(db, actor, challenge.shipment_id)
    if actor.id != challenge.receiver_id:
        raise HTTPException(404, "Challenge not found for this receiver.")
    if (
        challenge.verified_at
        or dt(challenge.expires_at) <= utcnow()
        or challenge.attempts >= 5
    ):
        raise HTTPException(
            409, "Challenge expired, already used or attempt limit reached."
        )
    challenge.attempts += 1
    digest = hashlib.scrypt(
        code.encode(), salt=bytes.fromhex(challenge.salt), n=16384, r=8, p=1
    ).hex()
    if not hmac.compare_digest(digest, challenge.otp_hash):
        db.commit()
        raise HTTPException(422, "OTP is incorrect.")
    challenge.verified_at = utcnow().isoformat()
    shipment.operational_data = {
        **shipment.operational_data,
        "pod_verified": True,
        "pod_receiver_id": actor.id,
        "pod_verified_at": challenge.verified_at,
        "pod_challenge_id": challenge.id,
    }
    audit(db, "delivery.verified", challenge.id, actor, shipment_id=shipment.id)
    db.commit()
    return {
        "verified": True,
        "receiver_id": actor.id,
        "verified_at": challenge.verified_at,
        "shipment_id": shipment.id,
    }
