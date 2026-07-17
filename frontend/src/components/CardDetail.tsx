"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TradeCard } from "@/lib/types";

export default function CardDetail({ cardId, onClose }: { cardId: number; onClose: () => void }) {
  const [card, setCard] = useState<TradeCard | null>(null);

  useEffect(() => {
    api.getCard(cardId).then(setCard).catch(() => setCard(null));
  }, [cardId]);

  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        {!card ? (
          <p className="text-zinc-400">Yükleniyor...</p>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{card.symbol}</h2>
              <button onClick={onClose} className="text-zinc-400 hover:text-zinc-100">
                ✕
              </button>
            </div>
            <p className="text-sm text-zinc-400">Durum: {card.status}</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>Giriş: {card.entry_zone_low}–{card.entry_zone_high}</div>
              <div>Stop: {card.stop}</div>
              <div>T1: {card.target_1}</div>
              <div>T2: {card.target_2}</div>
              <div>Vade: {card.horizon}</div>
              <div>Güven: {card.confidence}</div>
            </div>
            {card.reasoning && <p className="text-sm text-zinc-300">💡 {card.reasoning}</p>}
            {card.catalyst && <p className="text-sm text-zinc-300">📰 {card.catalyst}</p>}
            {card.news_context && card.news_context.length > 0 && (
              <div>
                <h3 className="mb-1 text-sm font-medium text-zinc-300">Haberler</h3>
                <ul className="space-y-1 text-xs text-zinc-400">
                  {card.news_context.map((n, i) => (
                    <li key={i}>{n.headline} — {n.source}</li>
                  ))}
                </ul>
              </div>
            )}
            <details className="text-xs text-zinc-500">
              <summary className="cursor-pointer">Ham snapshot verisi</summary>
              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(card.snapshot, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}
