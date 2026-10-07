from datetime import timedelta
from sqlalchemy import select
from backend.models import (CargoRequest, CargoVoyage, LineQuote, QuoteAcceptance,
    ProviderJob, Booking, InvoiceRecord, TerminalRateCard, TerminalCapability, CargoLoadProfile, TruckResource, Vessel)
from backend.services.timeutils import utcnow, dt

CONTROL = {"X-Demo-Role": "control"}
OPERATOR = {"X-Demo-Role": "operator"}


def post(client, path, body=None, headers=None, expected=200):
    result = client.post(f"/api/lines{path}", json=body, headers=headers)
    assert result.status_code == expected, result.text
    return result.json()


def proposed(client, cargo_ids=None):
    return post(client, "/proposals", {"cargo_ids": cargo_ids or ["hero-cargo", "pool-cargo"], "vessel_id": "vembanad"}, expected=201)


def accepted(client, voyage=None):
    voyage = voyage or proposed(client)
    for member in voyage["members"]:
        post(client, f"/quotes/{member['quote']['id']}/approve")
    post(client, f"/{voyage['id']}/operator-response", {"version": voyage["version"], "accept": True}, OPERATOR)
    for job in voyage["jobs"]:
        post(client, f"/jobs/{job['id']}/response", {"status": "ACCEPTED"}, CONTROL)
    return post(client, f"/{voyage['id']}/confirm")


def test_three_role_locked_bundle_and_receipts(client, db):
    voyage = proposed(client)
    pickup = [j for j in voyage["jobs"] if j["kind"] == "PICKUP_TRUCK"]
    assert len(pickup) == 4
    actual_jobs = [db.get(ProviderJob, j["id"]) for j in pickup]
    assert len({j.truck_resource_id for j in actual_jobs}) == 4
    quotes = [db.get(LineQuote, m["quote"]["id"]) for m in voyage["members"]]
    assert sum(q.snapshot["breakdown_minor"]["sailing_fixed"] for q in quotes) == 1200000
    assert sum(q.snapshot["breakdown_minor"]["origin_handling_setup"] for q in quotes) == 150000
    post(client, f"/{voyage['id']}/confirm", expected=409)
    post(client, f"/{voyage['id']}/operator-response", {"version": 1, "accept": True}, OPERATOR, expected=409)
    confirmed = accepted(client, voyage)
    repeat = post(client, f"/{voyage['id']}/confirm")
    assert [m["booking_id"] for m in repeat["members"]] == [m["booking_id"] for m in confirmed["members"]]
    for member in confirmed["members"]:
        assert round(member["invoice"]["total"] * 100) == member["quote"]["total_minor"]
        assert member["invoice"]["line_items"] == member["quote"]["snapshot"]["breakdown"]
        post(client, f"/{voyage['id']}/receipt", {"cargo_id": member["cargo_id"], "quantity_tonnes": member["weight_tonnes"], "receiver_name": "Kochi Builder"}, CONTROL, expected=409)
    for state in ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING"]:
        post(client, f"/{voyage['id']}/milestone", {"status": state}, CONTROL)
    for member in confirmed["members"]:
        result = post(client, f"/{voyage['id']}/receipt", {"cargo_id": member["cargo_id"], "quantity_tonnes": member["weight_tonnes"], "receiver_name": "Kochi Builder"}, CONTROL)
    assert result["status"] == "COMPLETED"
    impact = client.get("/api/lines", headers=CONTROL).json()["impact"]
    assert impact["selected_water_tonnes"] == impact["completed_water_tonnes"] == 138
    assert impact["connecting_truck_trips"] == 4


def test_first_member_cancellation_keeps_shared_jobs_and_other_price(client, db):
    voyage = accepted(client)
    first, second = voyage["members"]
    original = second["quote"]["total_minor"]
    result = post(client, f"/{voyage['id']}/cancel", {"cargo_id": first["cargo_id"]})
    assert result["status"] == "CONFIRMED"
    assert result["weight_tonnes"] == second["weight_tonnes"]
    assert all(j["status"] == "ACCEPTED" for j in result["jobs"] if j["cargo_id"] is None)
    assert result["members"][1]["quote"]["total_minor"] == original
    # Common resource intervals still prevent an overlapping second departure.
    from backend.services.terminal_resources import reservations
    from backend.models import TerminalResource
    common = next(db.get(ProviderJob, j["id"]) for j in result["jobs"] if j["cargo_id"] is None)
    assert common.id in {r.id for r in reservations(db, db.get(TerminalResource, common.terminal_resource_id), [])}


def test_quote_expiry_decline_and_owner_scope(client, db):
    voyage = proposed(client)
    quote = voyage["members"][0]["quote"]
    assert client.post(f"/api/lines/quotes/{quote['id']}/approve", headers={"X-Demo-User": "competitor-user"}).status_code == 404
    assert client.post("/api/lines/proposals", json={"cargo_ids": ["unserved-cargo"], "vessel_id": "vembanad"}, headers=CONTROL).status_code == 404
    assert client.get("/api/cargo/unserved-cargo/compare?vessel_id=vembanad", headers=CONTROL).status_code == 404
    assert all(c["id"] != "unserved-cargo" for c in client.get("/api/workspace", headers=CONTROL).json()["cargo"])
    post(client, f"/jobs/{voyage['jobs'][0]['id']}/response", {"status": "DECLINED"}, CONTROL)
    assert all(j.status not in {"PENDING", "ACCEPTED"} for j in db.scalars(select(ProviderJob)))
    post(client, f"/{voyage['id']}/confirm", expected=409)
    another = proposed(client)
    db.get(CargoVoyage, another["id"]).expires_at = (utcnow() - timedelta(seconds=1)).isoformat()
    db.commit()
    post(client, f"/quotes/{another['members'][0]['quote']['id']}/approve", expected=409)
    assert db.get(CargoVoyage, another["id"]).status == "EXPIRED"
    assert all(j.status not in {"PENDING", "ACCEPTED"} for j in db.scalars(select(ProviderJob)))


def test_stale_cargo_requires_new_quote_and_new_card_keeps_old_terms(client, db):
    voyage = proposed(client)
    cargo = db.get(CargoRequest, "hero-cargo")
    cargo.weight_tonnes = 79
    db.commit()
    post(client, f"/quotes/{voyage['members'][0]['quote']['id']}/approve", expected=409)
    cargo.weight_tonnes = 80
    old = db.get(TerminalRateCard, voyage["members"][0]["quote"]["snapshot"]["rate_card_ids"][0])
    db.add(TerminalRateCard(id="new-rate-card", terminal_id=old.terminal_id, version=2, terms={**old.terms, "setup_minor": 900000}))
    db.commit()
    # A separate new availability listing must not silently substitute this quote's listing.
    from backend.models import VesselAvailability
    from backend.repositories.common import record
    prior = db.get(VesselAvailability, db.get(CargoVoyage, voyage["id"]).plan["availability_id"])
    db.add(VesselAvailability(**{**record(prior), "id": "availability-000-new-listing"}))
    db.commit()
    result = accepted(client, voyage)
    assert result["members"][0]["quote"]["total_minor"] == voyage["members"][0]["quote"]["total_minor"]


def test_missing_destination_trucks_and_real_piece_limit(client, db):
    hero = db.get(CargoRequest, "hero-cargo")
    hero.last_mile_required = True
    hero.destination_coordinates = [9.55, 76.37]
    # Four first and four last trucks must be persisted, even at a nearby terminal.
    db.commit()
    voyage = proposed(client)
    assert len([j for j in voyage["jobs"] if j["kind"] == "DELIVERY_TRUCK"]) == 4
    for member in voyage["members"]:
        post(client, f"/quotes/{member['quote']['id']}/approve")
    post(client, f"/{voyage['id']}/operator-response", {"version": 1, "accept": True}, OPERATOR)
    for job in voyage["jobs"]:
        if job["kind"] != "DELIVERY_TRUCK":
            post(client, f"/jobs/{job['id']}/response", {"status": "ACCEPTED"}, CONTROL)
    post(client, f"/{voyage['id']}/confirm", expected=409)
    post(client, f"/{voyage['id']}/cancel", {})
    for cap in db.scalars(select(TerminalCapability)):
        cap.crane_capacity = 10
    db.scalar(select(CargoLoadProfile).where(CargoLoadProfile.cargo_id == "pool-cargo")).heaviest_piece_tonnes = 12
    db.commit()
    result = client.post("/api/lines/proposals", json={"cargo_ids": ["pool-cargo"], "vessel_id": "vembanad"})
    assert result.status_code == 409
    assert "12 t piece" in result.text and "10 t" in result.text


def test_shared_water_different_door_eta(client, db):
    hero = db.get(CargoRequest, "hero-cargo")
    hero.last_mile_required = True
    hero.destination_coordinates = [9.55, 76.37]
    db.commit()
    voyage = proposed(client)
    first, second = voyage["members"]
    assert first["quote"]["snapshot"]["water_end"] == second["quote"]["snapshot"]["water_end"]
    assert dt(first["eta"]) > dt(second["eta"])


def test_model_reports_loss_even_at_high_fill(client, db):
    db.get(Vessel, "vembanad").rate_per_tonne_km = .1
    db.commit()
    voyage = proposed(client)
    operator_view = client.get("/api/lines", headers=OPERATOR).json()["departures"][0]
    assert operator_view["utilization"] == .92
    assert operator_view["projected_economics"]["contribution_minor"] < 0
    for member in voyage["members"]:
        post(client, f"/quotes/{member['quote']['id']}/approve")
    post(client, f"/{voyage['id']}/operator-response", {"version": 1, "accept": True}, OPERATOR, expected=409)


def test_fresh_small_cargo_can_book_after_explicit_operator_shortfall_acceptance(client, db):
    from backend.repositories.common import record
    original = record(db.get(CargoRequest, "hero-cargo"))
    fields = {key: original[key] for key in ["cargo_type", "packaging", "origin", "destination", "ready_time", "delivery_deadline", "first_mile_required", "last_mile_required"]}
    cargo = post(client, "/cargo", {
        "cargo": {**fields, "weight_tonnes": 1, "volume_m3": 2, "consolidation_allowed": False},
        "load_profile": {"heaviest_piece_tonnes": .05, "pieces": 20, "unit_length_m": .6, "unit_width_m": .4, "unit_height_m": .2},
    }, expected=201)
    voyage = proposed(client, [cargo["id"]])
    assert len(voyage["members"]) == 1
    quote = voyage["members"][0]["quote"]
    post(client, f"/quotes/{quote['id']}/approve")
    body = {"version": voyage["version"], "accept": True}
    post(client, f"/{voyage['id']}/operator-response", body, OPERATOR, expected=409)
    body["acknowledge_shortfall"] = True
    post(client, f"/{voyage['id']}/operator-response", body, {**OPERATOR, "X-Demo-User": "demo-pamba-operator"}, expected=404)
    accepted_voyage = post(client, f"/{voyage['id']}/operator-response", body, OPERATOR)
    assert accepted_voyage["operator_accepted"]
    post(client, f"/{voyage['id']}/confirm", headers=CONTROL, expected=409)
    assert any(job["kind"] == "PICKUP_TRUCK" for job in voyage["jobs"])
    for job in voyage["jobs"]:
        post(client, f"/jobs/{job['id']}/response", {"status": "ACCEPTED"}, CONTROL)
    booked = post(client, f"/{voyage['id']}/confirm", headers=CONTROL)
    assert db.get(CargoRequest, cargo["id"]).status == "CONFIRMED"
    assert round(booked["members"][0]["invoice"]["total"] * 100) == quote["total_minor"]
    for state in ["SCHEDULED", "LOADING", "IN_TRANSIT", "UNLOADING"]:
        post(client, f"/{voyage['id']}/milestone", {"status": state}, CONTROL)
    result = post(client, f"/{voyage['id']}/receipt", {"cargo_id": cargo["id"], "quantity_tonnes": 1, "receiver_name": "Small cargo receiver"}, CONTROL)
    assert result["status"] == "COMPLETED"
    assert db.get(Booking, booked["members"][0]["booking_id"]).status == "DELIVERED"


def test_provider_capacity_change_and_legacy_bypass_blocked(client, db):
    voyage = proposed(client)
    assert client.post("/api/bookings", json={"cargo_id": "hero-cargo", "vessel_id": "vembanad", "approved": True}).status_code == 409
    for member in voyage["members"]:
        post(client, f"/quotes/{member['quote']['id']}/approve")
    post(client, f"/{voyage['id']}/operator-response", {"version": 1, "accept": True}, OPERATOR)
    for job in voyage["jobs"]:
        post(client, f"/jobs/{job['id']}/response", {"status": "ACCEPTED"}, CONTROL)
    truck_job = next(db.get(ProviderJob, j["id"]) for j in voyage["jobs"] if j["kind"] == "PICKUP_TRUCK")
    db.get(TruckResource, truck_job.truck_resource_id).active = False
    db.commit()
    post(client, f"/{voyage['id']}/confirm", expected=409)


def test_pre_pickup_recovery_requotes_and_requires_replacement_operator(client, db):
    voyage = accepted(client)
    withdrawn = post(client, f"/{voyage['id']}/disrupt", {}, CONTROL)
    assert withdrawn["status"] == "DISRUPTED"
    assert all(m["invoice"]["status"] == "VOID" for m in withdrawn["members"])
    offers = client.get(f"/api/lines/{voyage['id']}/recovery-options", headers=CONTROL).json()
    replacement = next(o for o in offers["options"] if o["vessel_id"] == "pamba")
    fresh = post(client, "/proposals", {"cargo_ids": replacement["cargo_ids"], "vessel_id": "pamba", "parent_id": voyage["id"]}, CONTROL, expected=201)
    assert fresh["parent_id"] == voyage["id"]
    assert all(not m["accepted"] for m in fresh["members"])
    for member in fresh["members"]:
        post(client, f"/quotes/{member['quote']['id']}/approve")
    post(client, f"/{fresh['id']}/operator-response", {"version": 1, "accept": True}, OPERATOR, expected=404)
    post(client, f"/{fresh['id']}/operator-response", {"version": 1, "accept": True}, {**OPERATOR, "X-Demo-User": "demo-pamba-operator"})
    for job in fresh["jobs"]:
        post(client, f"/jobs/{job['id']}/response", {"status": "ACCEPTED"}, CONTROL)
    post(client, f"/{fresh['id']}/confirm", headers=CONTROL)
    post(client, f"/{fresh['id']}/milestone", {"status": "SCHEDULED"}, CONTROL)
    post(client, f"/{fresh['id']}/milestone", {"status": "LOADING"}, CONTROL)
    post(client, f"/{fresh['id']}/disrupt", {}, CONTROL, expected=409)


def test_receiving_window_and_actual_crossover_sampling(client, db):
    profile = db.scalar(select(CargoLoadProfile).where(CargoLoadProfile.cargo_id == "hero-cargo"))
    cargo = db.get(CargoRequest, "hero-cargo")
    profile.receiving_until = (dt(cargo.ready_time) + timedelta(hours=4)).isoformat()
    db.commit()
    post(client, "/proposals", {"cargo_ids": ["hero-cargo"], "vessel_id": "vembanad"}, expected=409)
    profile.receiving_until = None
    db.commit()
    result = client.get("/api/lines/cargo/hero-cargo/advice?vessel_id=vembanad&crossover=true")
    assert result.status_code == 200, result.text
    ranges = result.json()["crossover_ranges_tonnes"]
    assert ranges  # Discrete trips create computed ranges in the disclosed fixture.
    assert result.json()["road"]["truck_trips"] == 4
    for low, high in ranges:
        assert 1 <= low <= high <= 150


def test_terminal_operating_hours_and_nearby_door_pickup(client, db):
    hero = db.get(CargoRequest, "hero-cargo")
    hero.origin = "Maradu"
    hero.origin_coordinates = [9.946, 76.325]
    db.commit()
    voyage = proposed(client)
    assert len([j for j in voyage["jobs"] if j["kind"] == "PICKUP_TRUCK"]) == 4
    assert voyage["members"][0]["quote"]["snapshot"]["mode"] == "HYBRID"
    post(client, f"/{voyage['id']}/cancel", {})
    destination_card = db.get(TerminalRateCard, voyage["members"][0]["quote"]["snapshot"]["rate_card_ids"][1])
    db.add(TerminalRateCard(id="closing-card", terminal_id=destination_card.terminal_id, version=2,
                            terms={**destination_card.terms, "operating_hours": ["08:00", "15:00"]}))
    db.commit()
    post(client, "/proposals", {"cargo_ids": ["hero-cargo", "pool-cargo"], "vessel_id": "vembanad"}, expected=409)


def test_quote_binds_assignment_and_coordinator_cannot_manage_foreign_assets(client, db):
    voyage = proposed(client)
    quote = voyage["members"][0]["quote"]
    assert sum(r["kind"] == "PICKUP_TRUCK" for r in quote["snapshot"]["resource_plan"]) == 4
    for member in voyage["members"]:
        post(client, f"/quotes/{member['quote']['id']}/approve")
    job = db.get(ProviderJob, voyage["jobs"][0]["id"])
    job.ends_at = (dt(job.ends_at) + timedelta(minutes=1)).isoformat()
    db.commit()
    post(client, f"/{voyage['id']}/operator-response", {"version": 1, "accept": True}, OPERATOR, expected=409)
    assert client.post("/api/fleet/optimize", json={"cargo_ids": ["unserved-cargo"], "vessel_ids": ["vembanad"]}, headers=CONTROL).status_code == 404
    assert all(c["id"] != "unserved-cargo" for c in client.get("/api/fleet/demand", headers=CONTROL).json()["cargo"])
    assert all(c["cargo_id"] != "unserved-cargo" for c in client.get("/api/intelligence/failed-demand", headers=CONTROL).json()["rows"])


def test_marketplace_cargo_posts_profile_atomically_and_can_schedule(client, db):
    from backend.repositories.common import record
    sample = record(db.get(CargoRequest, "hero-cargo"))
    cargo = {key: sample[key] for key in ["cargo_type", "weight_tonnes", "volume_m3", "packaging", "origin", "destination", "ready_time", "delivery_deadline", "first_mile_required", "last_mile_required"]}
    profile = {"heaviest_piece_tonnes": .05, "pieces": 1600, "unit_length_m": 1, "unit_width_m": 1, "unit_height_m": 1}
    before = len(list(db.scalars(select(CargoRequest))))
    post(client, "/cargo", {"cargo": cargo, "load_profile": {**profile, "pieces": 1}}, expected=422)
    assert len(list(db.scalars(select(CargoRequest)))) == before
    post(client, "/cargo", {"cargo": {**cargo, "volume_m3": None}, "load_profile": profile}, expected=422)
    result = post(client, "/cargo", {"cargo": cargo, "load_profile": profile}, expected=201)
    assert db.scalar(select(CargoLoadProfile).where(CargoLoadProfile.cargo_id == result["id"])) is not None
    advice = client.get(f"/api/lines/cargo/{result['id']}/advice?vessel_id=vembanad").json()
    assert advice["water"]["feasible"]
    voyage = proposed(client, [result["id"], "pool-cargo"])
    assert {m["cargo_id"] for m in voyage["members"]} == {result["id"], "pool-cargo"}


def test_preferred_departure_is_checked_and_survives_confirmation(client, db):
    baseline = client.get("/api/lines/cargo/hero-cargo/advice?vessel_id=vembanad").json()["water"]
    preferred = (dt(baseline["departure"]) + timedelta(minutes=30)).isoformat()
    advice = client.get("/api/lines/cargo/hero-cargo/advice", params={"vessel_id": "vembanad", "not_before": preferred}).json()
    assert dt(advice["water"]["departure"]) >= dt(preferred)
    voyage = post(client, "/proposals", {"cargo_ids": ["hero-cargo", "pool-cargo"], "vessel_id": "vembanad", "not_before": preferred}, expected=201)
    assert dt(voyage["departure"]) >= dt(preferred)
    confirmed = accepted(client, voyage)
    assert confirmed["status"] == "CONFIRMED"
    post(client, "/proposals", {"cargo_ids": ["return-cargo"], "vessel_id": "vembanad", "not_before": "2026-10-08T12:00:00"}, expected=422)


def test_selected_boat_listing_is_pinned_and_wrong_boat_is_rejected(client, db):
    from backend.models import VesselAvailability
    listing = db.scalar(select(VesselAvailability).where(VesselAvailability.vessel_id == "vembanad", VesselAvailability.destination == "Alappuzha"))
    assert listing
    result = post(client, "/proposals", {"cargo_ids": ["hero-cargo", "pool-cargo"], "vessel_id": "vembanad", "availability_id": listing.id}, expected=201)
    assert db.get(CargoVoyage, result["id"]).plan["availability_id"] == listing.id
    assert accepted(client, result)["status"] == "CONFIRMED"
    wrong = client.get("/api/lines/cargo/return-cargo/advice", params={"vessel_id": "pamba", "availability_id": listing.id})
    assert wrong.status_code == 200
    assert wrong.json()["water"] is None
    assert "not found" in " ".join(wrong.json()["water_rejection_reasons"])
