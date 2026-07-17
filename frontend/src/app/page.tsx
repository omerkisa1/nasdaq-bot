"use client";

import { useEffect, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import StatusBar from "@/components/StatusBar";
import TradeCard from "@/components/TradeCard";
import CardDetail from "@/components/CardDetail";
import HistoryList from "@/components/HistoryList";
import StatsPanel from "@/components/StatsPanel";
import ScanLog from "@/components/ScanLog";
import SettingsPanel from "@/components/SettingsPanel";
import Toast from "@/components/Toast";

type Tab = "history" | "stats" | "scanlog" | "settings";

export default function Page() {
  const cards = useStore((s) => s.cards);
  const setCards = useStore((s) => s.setCards);
  const setStats = useStore((s) => s.setStats);
  const setSettings = useStore((s) => s.setSettings);
  const setScanRuns = useStore((s) => s.setScanRuns);
  const setHealth = useStore((s) => s.setHealth);

  const [tab, setTab] = useState<Tab>("history");
  const [detailId, setDetailId] = useState<number | null>(null);

  useWebSocket();

  useEffect(() => {
    api.getCards().then(setCards).catch(() => {});
    api.getStats().then(setStats).catch(() => {});
    api.getSettings().then(setSettings).catch(() => {});
    api.getScanRuns().then(setScanRuns).catch(() => {});
    api.getHealth().then(setHealth).catch(() => {});

    const poll = setInterval(() => {
      api.getHealth().then(setHealth).catch(() => {});
    }, 30000);
    return () => clearInterval(poll);
  }, [setCards, setStats, setSettings, setScanRuns, setHealth]);

  const activeCards = cards
    .filter((c) => c.status === "ACTIVE")
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  return (
    <div className="mx-auto max-w-3xl pb-16">
      <StatusBar />

      <section className="px-4 py-4">
        <h2 className="mb-3 text-sm font-medium text-zinc-400">Aktif Kartlar</h2>
        {activeCards.length === 0 ? (
          <p className="rounded-lg border border-dashed border-zinc-800 px-4 py-8 text-center text-sm text-zinc-500">
            Tarayıcı setup arıyor... Son tarama sonuçları için Tarama Logları sekmesine bakabilirsin.
          </p>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {activeCards.map((card) => (
                <TradeCard key={card.id} card={card} onOpenDetail={setDetailId} />
              ))}
            </AnimatePresence>
          </div>
        )}
      </section>

      <section className="px-4">
        <div className="mb-3 flex gap-2 border-b border-zinc-800 text-sm">
          {(
            [
              ["history", "Geçmiş"],
              ["stats", "İstatistik"],
              ["scanlog", "Tarama Logları"],
              ["settings", "Ayarlar"],
            ] as [Tab, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`border-b-2 px-3 py-2 ${
                tab === key ? "border-sky-400 text-sky-300" : "border-transparent text-zinc-500"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === "history" && <HistoryList />}
        {tab === "stats" && <StatsPanel />}
        {tab === "scanlog" && <ScanLog />}
        {tab === "settings" && <SettingsPanel />}
      </section>

      {detailId != null && <CardDetail cardId={detailId} onClose={() => setDetailId(null)} />}
      <Toast />
    </div>
  );
}
