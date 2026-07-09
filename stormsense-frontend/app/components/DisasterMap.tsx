"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { DisasterEvent } from "../lib/api";

const RISK_COLORS: Record<string, string> = {
  Low: "#22c55e",
  Medium: "#eab308",
  High: "#ef4444",
  Critical: "#ef4444",
};

const RISK_LABELS: Record<string, string> = {
  Low: "Low risk",
  Medium: "Medium risk",
  High: "High risk",
  Critical: "Critical risk",
};

// React/flexbox layouts can settle their final size *after* Leaflet has
// already measured its container, which leaves the map's internal size
// cache stale — this makes dragging feel broken/limited (it thinks the
// container is smaller than it really is). Watching the container with a
// ResizeObserver and calling invalidateSize() keeps it in sync.
function MapResizeHandler() {
  const map = useMap();

  useEffect(() => {
    const container = map.getContainer();
    map.invalidateSize();

    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });
    observer.observe(container);

    return () => observer.disconnect();
  }, [map]);

  return null;
}

interface DisasterMapProps {
  events: DisasterEvent[];
  onSelect: (event: DisasterEvent) => void;
}

export default function DisasterMap({ events, onSelect }: DisasterMapProps) {
  return (
    <MapContainer
      center={[20, 10]}
      zoom={2.3}
      // Fractional zoom + finer scroll steps make zooming feel smooth instead
      // of jumping between whole zoom levels.
      zoomSnap={0.5}
      zoomDelta={0.75}
      wheelPxPerZoomLevel={100}
      scrollWheelZoom={true}
      dragging={true}
      inertia={true}
      worldCopyJump={true}
      style={{ height: "100%", width: "100%", background: "#0b1220" }}
    >
      <MapResizeHandler />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      {events.map((event) => {
        const isSevere = event.risk === "Critical" || event.risk === "High";
        return (
          <CircleMarker
            key={event.id}
            center={[event.lat, event.lng]}
            radius={isSevere ? 10 : 6}
            className={isSevere ? "marker-pulse" : undefined}
            pathOptions={{
              color: RISK_COLORS[event.risk] || RISK_COLORS.Low,
              fillColor: RISK_COLORS[event.risk] || RISK_COLORS.Low,
              fillOpacity: 0.8,
              weight: 2,
            }}
            eventHandlers={{ click: () => onSelect(event) }}
          >
            <Popup>
              <div style={{ fontSize: "12px", lineHeight: 1.5 }}>
                <strong style={{ textTransform: "capitalize" }}>{event.type}</strong>
                {" — "}
                {RISK_LABELS[event.risk] || event.risk}
                <br />
                {event.location}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
