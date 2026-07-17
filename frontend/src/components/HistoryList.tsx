"use client";

import { useMemo, useState } from "react";
import { useStore } from "@/lib/store";
import type { CardStatus } from "@/lib/types";

const RESULT_BADGE: Record<string, { label: string; className: string }> = {
  TARGET_HIT: { label: "✅", className: "text-emerald-400" },
  STOP_HIT: { label: "❌", className: "text-red-400" },
  EXPIRED: { label: "⏱", className: "text-amber-400" },
  NO_FILL: { label: "⊘", className: "text-zinc-500" },
  CANCELLED: { label: "🚫", className: "text-zinc-500" },
};

export default function HistoryList() {
  const cards = useStore((s) => s.cards);
  const [filter, setFilter] = useState<CardStatus | "ALL">("ALL");

  const closed = useMemo(
    () =>
      cards
        .filter((c) => c.status !== "ACTIVE")
        .filter((c) => filter === "ALL" || c.status === filter)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [cards, filter]
  );

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2 text-xs">
        {(["ALL", "TARGET_HIT", "STOP_HIT", "EXPIRED", "NO_FILL", "CANCELLED"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`rounded-full border px-3 py-1 ${
              filter === s ? "border-zinc-400 bg-zinc-800" : "border-zinc-700 text-zinc-400"
            }`}
          >
            {s === "ALL" ? "Tümü" : s}
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {closed.length === 0 && <p className="text-sm text-zinc-500">Kapalı kart yok.</p>}
        {closed.map((c) => {
          const badge = RESULT_BADGE[c.status];
          return (
            <div
              key={c.id}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
            >
              <div className="flex items-center gap-2">
                <span className={badge?.className}>{badge?.label}</span>
                <span className="font-medium">{c.symbol}</span>
                <span className="text-xs text-zinc-500">{c.horizon}</span>
              </div>
              <span className={c.realized_r != null && c.realized_r >= 0 ? "text-emerald-400" : "text-red-400"}>
                {c.realized_r != null ? `${c.realized_r >= 0 ? "+" : ""}${c.realized_r}R` : "-"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
