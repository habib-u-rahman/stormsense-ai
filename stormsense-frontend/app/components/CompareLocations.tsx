"use client";

import { useState } from "react";
import { Scale, Plus, X, AlertTriangle } from "lucide-react";
import { compareLocations, CompareLocationResult } from "../lib/api";

const MIN_LOCATIONS = 2;
const MAX_LOCATIONS = 4;

const DEFAULT_LOCATIONS = ["Tokyo, Japan", "Los Angeles, USA"];

function getRiskPillClass(risk: string) {
  switch (risk) {
    case "Low": return "risk-low";
    case "Medium": return "risk-medium";
    case "High": return "risk-high";
    case "Critical": return "risk-critical";
    default: return "risk-medium";
  }
}

export default function CompareLocations() {
  const [locations, setLocations] = useState<string[]>(DEFAULT_LOCATIONS);
  const [results, setResults] = useState<CompareLocationResult[] | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const updateLocation = (index: number, value: string) => {
    setLocations((prev) => prev.map((loc, i) => (i === index ? value : loc)));
  };

  const addLocation = () => {
    if (locations.length >= MAX_LOCATIONS) return;
    setLocations((prev) => [...prev, ""]);
  };

  const removeLocation = (index: number) => {
    if (locations.length <= MIN_LOCATIONS) return;
    setLocations((prev) => prev.filter((_, i) => i !== index));
  };

  const runComparison = async () => {
    const cleaned = locations.map((l) => l.trim()).filter(Boolean);
    if (cleaned.length < MIN_LOCATIONS) {
      setFormError(`Enter at least ${MIN_LOCATIONS} locations to compare.`);
      return;
    }
    setFormError(null);
    setIsRunning(true);
    setResults(null);
    try {
      const data = await compareLocations(cleaned);
      setResults(data);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="glass rounded-3xl p-5">
      <div className="flex items-center gap-2 mb-1 px-1">
        <Scale className="w-5 h-5 text-[#3b82f6]" />
        <div className="font-semibold">Compare Risk Across Locations</div>
      </div>
      <div className="text-xs text-[#94a3b8] mb-4 px-1">
        Runs the real pipeline for each location at once — independent of the live map above.
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {locations.map((loc, i) => (
          <div key={i} className="flex items-center gap-1.5 bg-[#111827] border border-[#2a3749] rounded-lg px-2.5 py-1.5">
            <input
              type="text"
              value={loc}
              onChange={(e) => updateLocation(i, e.target.value)}
              placeholder={`Location ${i + 1}`}
              className="bg-transparent text-xs w-32 sm:w-36 placeholder:text-[#64748b] focus:outline-none"
            />
            {locations.length > MIN_LOCATIONS && (
              <button
                onClick={() => removeLocation(i)}
                aria-label={`Remove location ${i + 1}`}
                className="text-[#64748b] hover:text-[#e2e8f0] shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ))}
        {locations.length < MAX_LOCATIONS && (
          <button
            onClick={addLocation}
            className="flex items-center gap-1 text-xs text-[#94a3b8] border border-dashed border-[#2a3749] rounded-lg px-3 py-1.5 hover:border-[#3b82f6]/50 hover:text-[#e2e8f0] transition-all"
          >
            <Plus className="w-3.5 h-3.5" /> Add location
          </button>
        )}
      </div>

      <button
        onClick={runComparison}
        disabled={isRunning}
        className="px-4 py-2 rounded-xl bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-50 disabled:cursor-not-allowed text-xs font-medium transition-all mb-4"
      >
        {isRunning ? "Running pipeline for each location…" : "Run Comparison"}
      </button>

      {formError && (
        <div className="mb-4 px-3 py-2 rounded-xl bg-[#7f1d1d]/40 border border-[#ef4444]/40 text-xs text-[#fca5a5] flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          {formError}
        </div>
      )}

      {results && (
        <div className="overflow-x-auto rounded-2xl border border-[#2a3749]">
          <table className="w-full text-xs min-w-[480px]">
            <thead>
              <tr className="border-b border-[#2a3749] text-[10px] text-[#64748b] uppercase tracking-wide">
                <th className="text-left px-4 py-3">Location</th>
                <th className="px-4 py-3">Overall</th>
                <th className="px-4 py-3">Earthquake</th>
                <th className="px-4 py-3">Flood</th>
                <th className="px-4 py-3">Wildfire</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.location} className="border-b border-[#2a3749]/50 last:border-0">
                  <td className="px-4 py-3 font-medium">{r.location}</td>
                  {r.error ? (
                    <td colSpan={4} className="px-4 py-3 text-center text-[#fca5a5]">{r.error}</td>
                  ) : (
                    <>
                      <td className="px-4 py-3 text-center"><span className={`inline-block px-2.5 py-1 rounded-lg text-[11px] font-semibold ${getRiskPillClass(r.overall_risk)}`}>{r.overall_risk}</span></td>
                      <td className="px-4 py-3 text-center"><span className={`inline-block px-2.5 py-1 rounded-lg text-[11px] font-semibold ${getRiskPillClass(r.earthquake_risk)}`}>{r.earthquake_risk}</span></td>
                      <td className="px-4 py-3 text-center"><span className={`inline-block px-2.5 py-1 rounded-lg text-[11px] font-semibold ${getRiskPillClass(r.flood_risk)}`}>{r.flood_risk}</span></td>
                      <td className="px-4 py-3 text-center"><span className={`inline-block px-2.5 py-1 rounded-lg text-[11px] font-semibold ${getRiskPillClass(r.wildfire_risk)}`}>{r.wildfire_risk}</span></td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
