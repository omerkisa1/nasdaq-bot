import type { AnalyzeResponse, Health, ScanRun, Settings, Stats, TradeCard } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `${options?.method || "GET"} ${path} failed: ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // gövde json değilse orijinal mesaj kalır
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  getCards: () => request<TradeCard[]>("/api/cards"),
  getCard: (id: number) => request<TradeCard>(`/api/cards/${id}`),
  cancelCard: (id: number) =>
    request<TradeCard>(`/api/cards/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "CANCELLED" }),
    }),
  getStats: () => request<Stats>("/api/stats"),
  getSettings: () => request<Settings>("/api/settings"),
  patchSettings: (patch: Partial<Settings>) =>
    request<Settings>("/api/settings", { method: "PATCH", body: JSON.stringify(patch) }),
  triggerScan: () => request<unknown>("/api/scan/trigger", { method: "POST" }),
  getScanRuns: () => request<ScanRun[]>("/api/scan/runs?limit=20"),
  getHealth: () => request<Health>("/api/health"),
  analyzeSymbol: (symbol: string) =>
    request<AnalyzeResponse>(`/api/analyze/${symbol}`, { method: "POST" }),
  acceptCardDraft: (symbol: string, cardDraft: TradeCard) =>
    request<TradeCard>(`/api/analyze/${symbol}/accept`, {
      method: "POST",
      body: JSON.stringify(cardDraft),
    }),
};
