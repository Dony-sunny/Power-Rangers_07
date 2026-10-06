import heapq
from datetime import timedelta
from sqlalchemy import select
from backend.models import WaterwaySegment, RouteRestriction
from backend.services.timeutils import dt
from optimization.config import UNDER_KEEL_MARGIN


def segment_failures(segment, vessel, restrictions, departure):
    reasons = []
    if segment.navigation_status != "OPEN":
        reasons.append(
            f"{segment.id}: route {segment.navigation_status.lower()} ({segment.restriction or 'operational restriction'})."
        )
    if vessel.loaded_draft + UNDER_KEEL_MARGIN > segment.available_depth + 1e-9:
        reasons.append(
            f"{segment.id}: draft {vessel.loaded_draft:.1f} m + {UNDER_KEEL_MARGIN:.1f} m safety margin exceeds demo depth {segment.available_depth:.1f} m."
        )
    if vessel.air_draft > segment.minimum_bridge_clearance:
        reasons.append(
            f"{segment.id}: air draft {vessel.air_draft:.1f} m exceeds bridge clearance {segment.minimum_bridge_clearance:.1f} m."
        )
    if vessel.beam * 2 > segment.minimum_width:
        reasons.append(
            f"{segment.id}: beam {vessel.beam:.1f} m fails configured two-beam channel width {segment.minimum_width:.1f} m."
        )
    # Conservative planning: exclude an edge for restrictions intersecting the
    # three-day candidate horizon. Never infer navigability from an LLM.
    for restriction in restrictions:
        if (
            restriction.segment_id == segment.id
            and restriction.status == "ACTIVE"
            and dt(restriction.starts_at) <= departure + timedelta(days=3)
            and dt(restriction.ends_at) > departure
        ):
            reasons.append(f"{segment.id}: {restriction.reason}.")
    return reasons


def route(db, source, destination, vessel=None, departure=None):
    segments = list(db.scalars(select(WaterwaySegment)))
    restrictions = list(db.scalars(select(RouteRestriction)))
    graph = {}
    rejected = []
    for segment in segments:
        failures = (
            segment_failures(segment, vessel, restrictions, departure) if vessel else []
        )
        if failures:
            rejected.extend(failures)
            continue
        graph.setdefault(segment.source_node, []).append(
            (segment.destination_node, segment)
        )
        graph.setdefault(segment.destination_node, []).append(
            (segment.source_node, segment)
        )
    queue = [(0.0, source, [], [source])]
    visited = set()
    while queue:
        distance, node, path, nodes = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)
        if node == destination:
            return {
                "passed": True,
                "distance_km": distance,
                "segments": path,
                "nodes": nodes,
                "reasons": [],
            }
        for neighbor, segment in sorted(graph.get(node, []), key=lambda item: item[0]):
            if neighbor not in visited:
                heapq.heappush(
                    queue,
                    (
                        distance + segment.distance_km,
                        neighbor,
                        path + [segment.id],
                        nodes + [neighbor],
                    ),
                )
    return {
        "passed": False,
        "distance_km": 0,
        "segments": [],
        "nodes": [],
        "reasons": list(dict.fromkeys(rejected))
        or ["No connected waterway route in the configured graph."],
    }


def lock_wait(db, path, departure, speed):
    elapsed = 0.0
    waits = []
    for segment_id in path:
        segment = db.get(WaterwaySegment, segment_id)
        arrival = departure + timedelta(hours=elapsed)
        if segment.lock_required:
            if segment.lock_close_hour <= segment.lock_open_hour:
                return None, [f"{segment.lock_name}: no usable lock window."]
            opening = arrival.replace(
                hour=segment.lock_open_hour, minute=0, second=0, microsecond=0
            )
            closing = arrival.replace(
                hour=min(segment.lock_close_hour, 23), minute=0, second=0, microsecond=0
            )
            if arrival < opening:
                wait = (opening - arrival).total_seconds() / 3600
            elif segment.lock_close_hour < 24 and arrival >= closing:
                wait = (opening + timedelta(days=1) - arrival).total_seconds() / 3600
            else:
                wait = 0
            elapsed += wait
            if wait:
                waits.append(
                    f"{segment.lock_name}: wait {wait:.2f} h for configured demo window."
                )
        elapsed += segment.distance_km / speed
    return elapsed, waits
