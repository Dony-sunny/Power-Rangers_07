from types import SimpleNamespace
from optimization.multimodal.trip_costs import trips, truck_charge, allocate, sailing_economics


def test_discrete_trip_and_minimum_semantics():
    cargo = SimpleNamespace(weight_tonnes=80, volume_m3=60, pieces=1600)
    assert trips(cargo) == 4
    assert truck_charge(cargo, 1) == 1000000
    cargo.volume_m3 = 241
    assert trips(cargo) == 5
    assert allocate(100, [1, 1, 1]) == [34, 33, 33]
    assert sailing_economics(58, 64, 3)["contribution_minor"] == -56000
    assert sailing_economics(138, 64, 3)["contribution_minor"] == 1224000
    units = SimpleNamespace(weight_tonnes=48, volume_m3=20, pieces=4, heaviest_piece_tonnes=12)
    assert trips(units) == 4
