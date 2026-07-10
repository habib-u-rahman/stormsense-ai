// Client for the StormSense AI FastAPI backend. REST calls are routed
// through the Next.js rewrite in next.config.ts (/api/backend/* -> backend);
// the WebSocket connects directly. Both point at NEXT_PUBLIC_API_URL
// (see .env.example), defaulting to localhost:8000 for local dev.

export interface DisasterEvent {
  id: string;
  type: "earthquake" | "flood" | "wildfire";
  location: string;
  magnitude?: number;
  severity?: string;
  lat: number;
  lng: number;
  risk: "Low" | "Medium" | "High" | "Critical";
  time: string;
  description: string;
}

export interface AnalyzeResponse {
  overall_risk: string;
  earthquake_risk: string;
  flood_risk: string;
  wildfire_risk: string;
  alert_triggered: boolean;
  alert_message: string;
  final_explanation: string;
  final_response: string;
  risk_trend?: string | null;
  events: DisasterEvent[];
}

export interface HistoryEntry {
  timestamp: string;
  overall_risk: string;
  earthquake_risk: string;
  flood_risk: string;
  wildfire_risk: string;
}

export async function analyze(query: string, location: string = ""): Promise<AnalyzeResponse> {
  const response = await fetch("/api/backend/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, location }),
  });

  if (!response.ok) {
    // FastAPI's HTTPException body is {"detail": "..."} — surface that
    // instead of a bare status code so failures are actually diagnosable.
    let detail: string | null = null;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // Not JSON — this happens when the Next.js proxy itself can't reach
      // the backend at all (it was never running, or it crashed), rather
      // than the backend returning a real error. Say so explicitly.
    }
    throw new Error(
      detail ?? "Cannot reach the backend. Make sure it's running: cd backend && uvicorn main:app --port 8000"
    );
  }

  return response.json();
}

export async function getHistory(): Promise<HistoryEntry[]> {
  const response = await fetch("/api/backend/api/history");
  if (!response.ok) {
    throw new Error(`Failed to load risk history (status ${response.status})`);
  }
  return response.json();
}

export async function subscribe(value: string): Promise<string> {
  const response = await fetch("/api/backend/api/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.detail || `Subscription failed (status ${response.status})`);
  }
  return body.message as string;
}

// The autonomous monitor's live push feed connects directly to the backend
// (not through the Next.js proxy, since WebSocket upgrades aren't reliably
// proxied in all deployment setups). NEXT_PUBLIC_API_URL lets this point
// at a deployed backend; falls back to the current host on port 8000 for
// local dev, matching the same convention as next.config.ts's rewrite.
export function getWebSocketUrl(): string {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL;
  if (backendUrl) {
    return backendUrl.replace(/^http/, "ws") + "/ws/live";
  }
  return `ws://${window.location.hostname}:8000/ws/live`;
}
