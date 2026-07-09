// Client for the StormSense AI FastAPI backend, routed through the
// Next.js rewrite in next.config.ts (/api/backend/* -> http://localhost:8000/*).

export interface AnalyzeResponse {
  overall_risk: string;
  earthquake_risk: string;
  flood_risk: string;
  wildfire_risk: string;
  alert_triggered: boolean;
  alert_message: string;
  final_explanation: string;
  final_response: string;
}

export async function analyze(query: string, location: string = ""): Promise<AnalyzeResponse> {
  const response = await fetch("/api/backend/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, location }),
  });

  if (!response.ok) {
    throw new Error(`Backend request failed with status ${response.status}`);
  }

  return response.json();
}
