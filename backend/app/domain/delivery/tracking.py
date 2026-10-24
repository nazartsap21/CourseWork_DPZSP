"""Simulated courier movement, computed on request.

There is no GPS: when the courier picks the order up we store the route and
the time. Later, the current position is the point that lies at the same
fraction of the route's length as the elapsed time is of the ride time.
Nothing runs in the background; every request recomputes it.
"""

from dataclasses import dataclass
from datetime import datetime
from math import ceil

from .geo import GeoPoint, haversine_km
from .strategies import ride_minutes


@dataclass(frozen=True)
class CourierPosition:
    point: GeoPoint
    progress: float  # 0.0 at the restaurant, 1.0 at the door
    minutes_left: int


def route_length_km(points: list[GeoPoint]) -> float:
    return sum(haversine_km(a, b) for a, b in zip(points, points[1:], strict=False))


def point_along(points: list[GeoPoint], fraction: float) -> GeoPoint:
    """The point at `fraction` of the polyline's length (0..1), interpolated linearly."""
    if fraction <= 0 or len(points) == 1:
        return points[0]
    if fraction >= 1:
        return points[-1]
    target = route_length_km(points) * fraction
    walked = 0.0
    for a, b in zip(points, points[1:], strict=False):
        segment = haversine_km(a, b)
        if segment > 0 and walked + segment >= target:
            t = (target - walked) / segment
            return GeoPoint(a.lat + (b.lat - a.lat) * t, a.lng + (b.lng - a.lng) * t)
        walked += segment
    return points[-1]


def courier_position(
    points: list[GeoPoint], picked_up_at: datetime, now: datetime
) -> CourierPosition:
    # Same ride-time formula the delivery strategies use for the ETA.
    ride = ride_minutes(route_length_km(points))
    elapsed = max((now - picked_up_at).total_seconds() / 60, 0)
    progress = min(elapsed / ride, 1.0)
    return CourierPosition(
        point=point_along(points, progress),
        progress=progress,
        minutes_left=max(ceil(ride - elapsed), 0),
    )
