"use client";

import "leaflet/dist/leaflet.css";

import { Circle, CircleMarker, MapContainer, TileLayer, Tooltip, useMapEvents } from "react-leaflet";

export interface MapPoint {
  lat: number;
  lng: number;
}

function ClickToPick({ onPick }: { onPick: (point: MapPoint) => void }) {
  useMapEvents({
    click(event) {
      onPick({ lat: event.latlng.lat, lng: event.latlng.lng });
    },
  });
  return null;
}

/**
 * Leaflet touches `window`, so this module is loaded with `dynamic(..., { ssr: false })`.
 * Colors come from CSS classes in globals.css (theme tokens), because Leaflet
 * writes SVG attributes that can't reference CSS variables directly. The class
 * must be a direct prop: react-leaflet applies `pathOptions` via `setStyle`,
 * which ignores `className`.
 */
export default function DeliveryMap({
  restaurant,
  point,
  radiusKm,
  onPick,
}: {
  restaurant: MapPoint & { name: string };
  point: MapPoint | null;
  radiusKm: number | null;
  onPick: (point: MapPoint) => void;
}) {
  return (
    <MapContainer
      center={[restaurant.lat, restaurant.lng]}
      zoom={14}
      scrollWheelZoom={false}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {radiusKm !== null && (
        <Circle
          center={[restaurant.lat, restaurant.lng]}
          radius={radiusKm * 1000}
          className="map-zone"
          interactive={false}
        />
      )}
      <CircleMarker center={[restaurant.lat, restaurant.lng]} radius={8} className="map-restaurant">
        <Tooltip direction="top" offset={[0, -8]}>
          {restaurant.name}
        </Tooltip>
      </CircleMarker>
      {point && (
        <CircleMarker center={[point.lat, point.lng]} radius={9} className="map-destination">
          <Tooltip direction="top" offset={[0, -8]} permanent>
            Deliver here
          </Tooltip>
        </CircleMarker>
      )}
      <ClickToPick onPick={onPick} />
    </MapContainer>
  );
}
