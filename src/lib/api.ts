import type { AnalysisResult } from "@/types";

export async function analyzeIdea(
  idea: string,
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
    signal,
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      typeof payload?.error === "string"
        ? payload.error
        : "Analysis service is unavailable.";
    throw new Error(message);
  }

  if (!payload || typeof payload !== 'object' || !('final_brief' in payload)) {
    throw new Error('Invalid analysis response from server.');
  }

  return payload as AnalysisResult;
}
