"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { DisasterEvent } from "../lib/api";

const RISK_COLORS: Record<string, string> = {
  Low: "#22c55e",
  Medium: "#eab308",
  High: "#ef4444",
  Critical: "#ef4444",
};

interface DisasterMapProps {
  events: DisasterEvent[];
  onSelect: (event: DisasterEvent) => void;
}

export default function DisasterMap({ events, onSelect }: DisasterMapProps) {
  return (
    <MapContainer
      center={[20, 10]}
      zoom={2}
      scrollWheelZoom={true}
      style={{ height: "100%", width: "100%", background: "#111827" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {events.map((event) => (
        <CircleMarker
          key={event.id}
          center={[event.lat, event.lng]}
          radius={event.risk === "Critical" || event.risk === "High" ? 9 : 6}
          pathOptions={{
            color: RISK_COLORS[event.risk] || RISK_COLORS.Low,
            fillColor: RISK_COLORS[event.risk] || RISK_COLORS.Low,
            fillOpacity: 0.75,
          }}
          eventHandlers={{ click: () => onSelect(event) }}
        >
          <Popup>
            <div style={{ fontSize: "12px" }}>
              <strong>{event.type.toUpperCase()}</strong> — {event.risk} risk
              <br />
              {event.location}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
