// Client for the StormSense AI FastAPI backend, routed through the
// Next.js rewrite in next.config.ts (/api/backend/* -> http://localhost:8000/*).

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
  events: DisasterEvent[];
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
