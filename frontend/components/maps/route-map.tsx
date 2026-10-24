"use client";

import "leaflet/dist/leaflet.css";

import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";

import type { LatLng } from "@/types/orders";

type Point = [number, number];

function FitToPoints({ points }: { points: Point[] }) {
  const map = useMap();
  // Keyed by value, so the map refits only when the route changes, not on every render.
  const key = JSON.stringify(points);
  useEffect(() => {
    const framed = JSON.parse(key) as Point[];
    if (framed.length >= 2) map.fitBounds(framed, { padding: [32, 32] });
  }, [map, key]);
  return null;
}

/**
 * Restaurant, destination, road route and the courier marker. Loaded with
 * `dynamic(..., { ssr: false })` because Leaflet needs `window`. Shapes take
 * their colors from `.map-*` classes in globals.css (theme tokens).
 */
export default function RouteMap({
  restaurant,
  destination,
  route,
  courier,
}: {
  restaurant: LatLng;
  destination: LatLng | null;
  route: Point[];
  courier: LatLng | null;
}) {
  const start: Point = [restaurant.lat, restaurant.lng];
  const end: Point | null = destination ? [destination.lat, destination.lng] : null;
  const framing = route.length >= 2 ? route : end ? [start, end] : [start];

  return (
    <MapContainer center={start} zoom={15} scrollWheelZoom={false} className="h-full w-full">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitToPoints points={framing} />
      {route.length >= 2 && <Polyline positions={route} className="map-route" />}
      <CircleMarker center={start} radius={8} className="map-restaurant">
        <Tooltip direction="top" offset={[0, -8]}>
          Restaurant
        </Tooltip>
      </CircleMarker>
      {end && (
        <CircleMarker center={end} radius={8} className="map-destination">
          <Tooltip direction="top" offset={[0, -8]}>
            Delivery point
          </Tooltip>
        </CircleMarker>
      )}
      {courier && (
        <CircleMarker center={[courier.lat, courier.lng]} radius={10} className="map-courier">
          <Tooltip direction="top" offset={[0, -10]} permanent>
            Courier
          </Tooltip>
        </CircleMarker>
      )}
    </MapContainer>
  );
}
