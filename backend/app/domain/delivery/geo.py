from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lng: float


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """Great-circle distance; a straight line, not a road route."""
    d_lat = radians(b.lat - a.lat)
    d_lng = radians(b.lng - a.lng)
    h = sin(d_lat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(d_lng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(h))
