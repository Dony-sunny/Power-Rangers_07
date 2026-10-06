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
