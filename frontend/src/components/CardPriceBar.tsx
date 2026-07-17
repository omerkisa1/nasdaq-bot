"use client";

import type { TradeCard } from "@/lib/types";

export default function CardPriceBar({ card }: { card: TradeCard }) {
  const { stop, entry_zone_low, entry_zone_high, target_1, target_2 } = card;
  const price = card.current_price ?? card.price_at_creation;

  const min = stop;
  const max = target_2;
  const range = max - min || 1;
  const pct = (value: number) => Math.min(100, Math.max(0, ((value - min) / range) * 100));

  const inZone = price >= entry_zone_low && price <= entry_zone_high;

  return (
    <div className="mt-3">
      <div className="flex justify-between text-[11px] text-zinc-500">
        <span>stop {stop.toFixed(2)}</span>
        <span className={inZone ? "font-semibold text-emerald-400" : ""}>
          giriş {entry_zone_low.toFixed(2)}–{entry_zone_high.toFixed(2)}
        </span>
        <span>T1 {target_1.toFixed(2)}</span>
        <span>T2 {target_2.toFixed(2)}</span>
      </div>
      <div className="relative mt-1 h-2 rounded-full bg-zinc-800">
        <div
          className={`absolute h-2 rounded-full transition-all duration-300 ${
            inZone ? "bg-emerald-500/40" : "bg-zinc-700"
          }`}
          style={{ left: `${pct(entry_zone_low)}%`, width: `${pct(entry_zone_high) - pct(entry_zone_low)}%` }}
        />
        <div
          className="absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full border-2 border-zinc-950 bg-sky-400 transition-all duration-300"
          style={{ left: `calc(${pct(price)}% - 6px)` }}
        />
      </div>
      <div className="mt-1 text-center text-xs text-zinc-400">şu an: ${price.toFixed(2)}</div>
    </div>
  );
}
