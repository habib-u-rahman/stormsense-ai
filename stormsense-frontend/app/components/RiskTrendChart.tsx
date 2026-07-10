"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { HistoryEntry } from "../lib/api";

const RISK_TO_INDEX: Record<string, number> = { Low: 0, Medium: 1, High: 2, Critical: 3 };
const RISK_LABELS = ["Low", "Medium", "High", "Critical"];
const SERIES_COLOR = "#3b82f6"; // the product's established brand blue, already used throughout the UI
const SURFACE_COLOR = "#111827"; // matches .map-container / card surfaces, for marker rings

const HEIGHT = 180;
const PADDING_LEFT = 46; // room for the Low/Medium/High/Critical axis labels
const PADDING_RIGHT = 12;
const PADDING_TOP = 14;
const PADDING_BOTTOM = 20;

interface RiskTrendChartProps {
  history: HistoryEntry[];
}

export default function RiskTrendChart({ history }: RiskTrendChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [width, setWidth] = useState(600);
  const containerRef = useRef<HTMLDivElement>(null);

  // Measure the container's real pixel width so the viewBox matches 1:1 —
  // avoids stretching/distorting circles and text via preserveAspectRatio.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      const newWidth = entries[0]?.contentRect.width;
      if (newWidth && newWidth > 0) setWidth(newWidth);
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const plotWidth = width - PADDING_LEFT - PADDING_RIGHT;
  const plotHeight = HEIGHT - PADDING_TOP - PADDING_BOTTOM;

  const points = useMemo(() => {
    if (history.length === 0) return [];
    return history.map((entry, i) => {
      const riskIndex = RISK_TO_INDEX[entry.overall_risk] ?? 0;
      const x = history.length === 1 ? PADDING_LEFT : PADDING_LEFT + (i / (history.length - 1)) * plotWidth;
      const y = PADDING_TOP + (1 - riskIndex / 3) * plotHeight;
      return { x, y, entry };
    });
  }, [history, plotWidth, plotHeight]);

  if (history.length < 2) {
    return (
      <div ref={containerRef} className="flex items-center justify-center h-[180px] text-sm text-[#64748b] text-center px-6">
        Building risk history — the autonomous monitor checks every few minutes.
        <br />
        Check back shortly to see the trend.
      </div>
    );
  }

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${points[points.length - 1].x.toFixed(1)},${(PADDING_TOP + plotHeight).toFixed(1)} L${points[0].x.toFixed(1)},${(PADDING_TOP + plotHeight).toFixed(1)} Z`;

  const handlePointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const relativeX = e.clientX - rect.left;
    // Snap to the nearest data point — readers aim at a time, not a 2px line.
    let nearest = 0;
    let nearestDist = Infinity;
    points.forEach((p, i) => {
      const dist = Math.abs(p.x - relativeX);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = i;
      }
    });
    setHoverIndex(nearest);
  };

  const hovered = hoverIndex !== null ? points[hoverIndex] : null;
  const last = points[points.length - 1];

  return (
    <div ref={containerRef} className="relative">
      <svg
        viewBox={`0 0 ${width} ${HEIGHT}`}
        className="w-full h-[180px]"
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setHoverIndex(null)}
      >
        {/* Y-axis gridlines + ordinal risk labels */}
        {RISK_LABELS.map((label, i) => {
          const y = PADDING_TOP + (1 - i / 3) * plotHeight;
          return (
            <g key={label}>
              <line x1={PADDING_LEFT} y1={y} x2={width - PADDING_RIGHT} y2={y} stroke="#2a3749" strokeWidth={1} />
              <text x={0} y={y} dy={3} fontSize={10} fill="#64748b">
                {label}
              </text>
            </g>
          );
        })}

        {/* Area fill: series hue at ~10% opacity */}
        <path d={areaPath} fill={SERIES_COLOR} fillOpacity={0.1} stroke="none" />

        {/* Line: 2px, round join/cap */}
        <path d={linePath} fill="none" stroke={SERIES_COLOR} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />

        {/* Current point marker, with a surface ring so it stays legible crossing the line */}
        <circle cx={last.x} cy={last.y} r={4} fill={SERIES_COLOR} stroke={SURFACE_COLOR} strokeWidth={2} />

        {/* Hover crosshair + marker */}
        {hovered && (
          <>
            <line
              x1={hovered.x}
              y1={PADDING_TOP}
              x2={hovered.x}
              y2={PADDING_TOP + plotHeight}
              stroke="#64748b"
              strokeWidth={1}
              strokeDasharray="3,3"
            />
            <circle cx={hovered.x} cy={hovered.y} r={4} fill={SERIES_COLOR} stroke={SURFACE_COLOR} strokeWidth={2} />
          </>
        )}
      </svg>

      {/* Tooltip: value leads, label follows */}
      {hovered && (
        <div
          className="absolute glass px-3 py-2 rounded-xl text-xs pointer-events-none z-10"
          style={{
            left: `${Math.min(85, Math.max(2, (hovered.x / width) * 100))}%`,
            top: 4,
            transform: hovered.x > width / 2 ? "translateX(-100%)" : undefined,
          }}
        >
          <div className="font-semibold">{hovered.entry.overall_risk}</div>
          <div className="text-[#64748b] mt-0.5">
            {new Date(hovered.entry.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
          </div>
        </div>
      )}
    </div>
  );
}
