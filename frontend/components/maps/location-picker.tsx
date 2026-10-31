"use client";

import "leaflet/dist/leaflet.css";

import { CircleMarker, MapContainer, TileLayer, useMapEvents } from "react-leaflet";

import type { LatLng } from "@/types/orders";

// Rynok Square, a sensible default centre for a new Lviv restaurant.
const LVIV_CENTER: [number, number] = [49.8419, 24.0316];

function ClickToPick({ onPick }: { onPick: (point: LatLng) => void }) {
  useMapEvents({ click: (event) => onPick({ lat: event.latlng.lat, lng: event.latlng.lng }) });
  return null;
}

/** Click to set a single point (e.g. a restaurant's location). Client-only, load via next/dynamic. */
export default function LocationPicker({ value, onChange }: { value: LatLng | null; onChange: (p: LatLng) => void }) {
  return (
    <MapContainer center={value ? [value.lat, value.lng] : LVIV_CENTER} zoom={15} scrollWheelZoom={false} className="h-full w-full">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {value && <CircleMarker center={[value.lat, value.lng]} radius={9} className="map-restaurant" />}
      <ClickToPick onPick={onChange} />
    </MapContainer>
  );
}
