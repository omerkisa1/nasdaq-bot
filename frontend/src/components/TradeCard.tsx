"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import type { TradeCard as TradeCardType } from "@/lib/types";
import { api } from "@/lib/api";
import { useStore } from "@/lib/store";
import CardPriceBar from "./CardPriceBar";

const HORIZON_LABEL: Record<string, string> = {
  "30m": "30dk",
  "2h": "2sa",
  "1d": "1g",
  "2d": "2g",
  "3d": "3g",
};

function remainingTime(expiresAt: string): string {
  const diffMs = new Date(expiresAt).getTime() - Date.now();
  if (diffMs <= 0) return "süre doldu";
  const totalMin = Math.floor(diffMs / 60000);
  const days = Math.floor(totalMin / (60 * 24));
  const hours = Math.floor((totalMin % (60 * 24)) / 60);
  const minutes = totalMin % 60;
  if (days > 0) return `${days}g ${hours}sa`;
  if (hours > 0) return `${hours}sa ${minutes}dk`;
  return `${minutes}dk`;
}

export default function TradeCard({ card, onOpenDetail }: { card: TradeCardType; onOpenDetail: (id: number) => void }) {
  const [remaining, setRemaining] = useState(() => remainingTime(card.expires_at));
  const upsertCard = useStore((s) => s.upsertCard);

  useEffect(() => {
    const timer = setInterval(() => setRemaining(remainingTime(card.expires_at)), 30000);
    return () => clearInterval(timer);
  }, [card.expires_at]);

  async function handleCancel() {
    const updated = await api.cancelCard(card.id);
    upsertCard(updated);
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-zinc-800 bg-zinc-900 p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-2">
          <span className="text-lg font-semibold">{card.symbol}</span>
          {card.company_name && <span className="text-sm text-zinc-500">· {card.company_name}</span>}
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <span className="text-emerald-400">🟢 LONG</span>
          <span>{HORIZON_LABEL[card.horizon]} vade</span>
          <span>güven {card.confidence.toFixed(2)}</span>
          {card.t1_hit && (
            <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-emerald-300">T1 ✓</span>
          )}
        </div>
      </div>

      <CardPriceBar card={card} />

      <div className="mt-3 text-xs text-zinc-400">
        Pozisyon: {card.position_size} lot · Risk: ${card.risk_amount.toFixed(0)} · R/R 1:
        {((card.target_1 - card.entry_zone_low) / (card.entry_zone_low - card.stop)).toFixed(1)}
      </div>

      {card.reasoning && (
        <p className="mt-2 text-sm text-zinc-300">💡 {card.reasoning}</p>
      )}
      {card.invalidation && (
        <p className="mt-1 text-xs text-amber-400">⚠️ Geçersizlik: {card.invalidation}</p>
      )}

      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-zinc-500">Kalan süre: {remaining}</span>
        <div className="flex gap-2">
          <button
            onClick={() => onOpenDetail(card.id)}
            className="rounded-md border border-zinc-700 px-2.5 py-1 text-xs hover:bg-zinc-800"
          >
            Detay
          </button>
          <button
            onClick={handleCancel}
            className="rounded-md border border-red-900 px-2.5 py-1 text-xs text-red-400 hover:bg-red-950"
          >
            İptal Et
          </button>
        </div>
      </div>
    </motion.div>
  );
}
