"""Adapter: road routes from OSRM behind our own `RouteProvider` interface.

OSRM returns GeoJSON `[lng, lat]` pairs, meters and seconds inside a
`routes[0]` envelope; the adapter turns that into a `Route` of `GeoPoint`s in
kilometres. A straight-line provider is the fallback, so a slow or unreachable
routing service never blocks a courier from picking an order up.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import requests

from ..errors import ExternalServiceError
from .geo import GeoPoint, haversine_km
from .strategies import ROUTE_DETOUR_FACTOR


class RoutingError(ExternalServiceError):
    code = "ROUTING_UNAVAILABLE"


@dataclass(frozen=True)
class Route:
    points: list[GeoPoint]
    distance_km: float
    provider: str


class RouteProvider(ABC):
    """Road route between two points."""

    @abstractmethod
    def route(self, origin: GeoPoint, destination: GeoPoint) -> Route: ...


HttpGet = Callable[[str, dict[str, Any], float], Any]


def _requests_get_json(url: str, params: dict[str, Any], timeout: float) -> Any:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


class OsrmRouteProvider(RouteProvider):
    """Calls the OSRM `route` service (router.project-osrm.org by default)."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 4.0,
        http_get: HttpGet = _requests_get_json,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._http_get = http_get

    def route(self, origin: GeoPoint, destination: GeoPoint) -> Route:
        # OSRM wants lng,lat order in the path.
        coordinates = f"{origin.lng},{origin.lat};{destination.lng},{destination.lat}"
        url = f"{self._base_url}/route/v1/driving/{coordinates}"
        try:
            payload = self._http_get(
                url, {"overview": "full", "geometries": "geojson"}, self._timeout
            )
        except (requests.RequestException, ValueError) as error:
            raise RoutingError("The routing service is unavailable.") from error
        if (
            not isinstance(payload, dict)
            or payload.get("code") != "Ok"
            or not payload.get("routes")
        ):
            raise RoutingError("The routing service found no route.")
        try:
            best = payload["routes"][0]
            points = [GeoPoint(lat=lat, lng=lng) for lng, lat in best["geometry"]["coordinates"]]
            distance_km = best["distance"] / 1000
        except (KeyError, TypeError, ValueError) as error:
            raise RoutingError("The routing service returned an unexpected answer.") from error
        if len(points) < 2:
            raise RoutingError("The routing service returned an empty route.")
        return Route(points=points, distance_km=distance_km, provider="osrm")


class StraightLineRouteProvider(RouteProvider):
    """Offline estimate: a straight line, with the same detour factor the
    delivery strategies use for fees, so the numbers stay consistent."""

    def route(self, origin: GeoPoint, destination: GeoPoint) -> Route:
        distance = haversine_km(origin, destination) * ROUTE_DETOUR_FACTOR
        return Route(points=[origin, destination], distance_km=distance, provider="straight_line")


class FallbackRouteProvider(RouteProvider):
    """Tries the primary provider and falls back on any routing failure."""

    def __init__(self, primary: RouteProvider, fallback: RouteProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    def route(self, origin: GeoPoint, destination: GeoPoint) -> Route:
        try:
            return self._primary.route(origin, destination)
        except RoutingError:
            return self._fallback.route(origin, destination)
