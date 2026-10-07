from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.config import ROOT
from backend.database import Base, get_db
from backend.main import app
from data.seed.network import seed


def test_simultaneous_booking_cannot_double_reserve():
    db_path = ROOT / "data" / f"test-reservation-{uuid4().hex}.db"
    engine = create_engine(
        "sqlite:///" + db_path.as_posix(),
        connect_args={"check_same_thread": False, "timeout": 20},
    )
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with sessions() as db:
        seed(db)

    def override():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:

            def reserve(_):
                return client.post(
                    "/api/bookings",
                    json={
                        "cargo_id": "hero-cargo",
                        "vessel_id": "vembanad",
                        "mode": "HYBRID",
                        "approved": True,
                    },
                ).status_code

            with ThreadPoolExecutor(max_workers=2) as pool:
                codes = list(pool.map(reserve, [1, 2]))
            assert sorted(codes) == [201, 409]
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
        db_path.unlink(missing_ok=True)


def test_simultaneous_line_proposals_serialize_vessel_and_trucks(tmp_path):
    from sqlalchemy import select, event
    from backend.models import CargoRequest, CargoLoadProfile, CargoVoyage, ProviderJob
    from backend.repositories.common import record
    from backend.services.terminal_resources import seed_resources
    engine = create_engine("sqlite:///" + str(tmp_path / "lines.db"), connect_args={"check_same_thread": False, "timeout": 20})
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with sessions() as db:
        seed(db)
        seed_resources(db)
        original = record(db.get(CargoRequest, "hero-cargo"))
        original["id"] = "another-80t-load"
        db.add(CargoRequest(**original))
        db.flush()
        db.add(CargoLoadProfile(id="second-profile", cargo_id=original["id"], heaviest_piece_tonnes=.05, pieces=1600))
        db.commit()
    def override():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            def reserve(cargo_id):
                return client.post("/api/lines/proposals", json={"cargo_ids": [cargo_id], "vessel_id": "vembanad"}).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:
                codes = list(pool.map(reserve, ["hero-cargo", "another-80t-load"]))
            assert sorted(codes) == [201, 409]
        with sessions() as db:
            assert len(list(db.scalars(select(CargoVoyage)))) == 1
            truck_jobs = list(db.scalars(select(ProviderJob).where(ProviderJob.kind == "PICKUP_TRUCK")))
            assert len(truck_jobs) == len({j.truck_resource_id for j in truck_jobs}) == 4
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
