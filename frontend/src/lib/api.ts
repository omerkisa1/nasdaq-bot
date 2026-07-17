import type { Health, ScanRun, Settings, Stats, TradeCard } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`${options?.method || "GET"} ${path} failed: ${res.status}`);
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
};
