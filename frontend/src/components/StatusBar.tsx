"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";

export default function StatusBar({ onAnalyze }: { onAnalyze: (symbol: string) => void }) {
  const [query, setQuery] = useState("");
  const health = useStore((s) => s.health);
  const stats = useStore((s) => s.stats);
  const settings = useStore((s) => s.settings);
  const cards = useStore((s) => s.cards);
  const setSettings = useStore((s) => s.setSettings);

  const activeCount = cards.filter((c) => c.status === "ACTIVE").length;
  const maxActive = settings?.max_active_cards ?? "-";
  const todayR = stats?.total_r ?? 0;
  const wr30d = stats?.last_30d;

  const lastScanText = health?.last_scan
    ? `${Math.max(0, Math.round((Date.now() - new Date(health.last_scan).getTime()) / 60000))}dk önce`
    : "henüz yok";

  async function toggleScan() {
    if (!settings) return;
    const updated = await api.patchSettings({ scan_enabled: !settings.scan_enabled });
    setSettings(updated);
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const symbol = query.trim().toUpperCase();
    if (!symbol) return;
    onAnalyze(symbol);
    setQuery("");
  }

  return (
    <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 bg-zinc-950/95 px-4 py-3 backdrop-blur">
      <div className="flex flex-wrap items-center gap-4 text-sm">
        <span className="flex items-center gap-1.5">
          <span
            className={`h-2 w-2 rounded-full ${health?.market_open ? "bg-emerald-500" : "bg-zinc-600"}`}
          />
          Piyasa: {health?.market_open ? "Açık" : "Kapalı"}
        </span>
        <span>
          Tarayıcı: {health?.scanner_running ? "Çalışıyor" : "Bekliyor"} (son: {lastScanText})
        </span>
        <span>
          Aktif: {activeCount}/{maxActive} kart
        </span>
        <span className={todayR >= 0 ? "text-emerald-400" : "text-red-400"}>
          Bugün: {todayR >= 0 ? "+" : ""}
          {todayR.toFixed(1)}R
        </span>
        {wr30d && (
          <span>
            30 gün WR: %{(wr30d.win_rate * 100).toFixed(0)} ({wr30d.wins}/{wr30d.wins + wr30d.losses})
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <form onSubmit={handleSearch} className="flex items-center gap-1">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Sembol ara (örn. CRVO)"
            className="w-40 rounded-md border border-zinc-700 bg-zinc-900 px-2.5 py-1.5 text-sm placeholder:text-zinc-600"
          />
          <button
            type="submit"
            className="rounded-md border border-zinc-700 px-2.5 py-1.5 text-sm hover:bg-zinc-800"
          >
            Analiz Et
          </button>
        </form>
        <button
          onClick={toggleScan}
          className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800"
        >
          {settings?.scan_enabled ? "⏸ Taramayı Durdur" : "▶ Taramayı Başlat"}
        </button>
      </div>
    </div>
  );
}
