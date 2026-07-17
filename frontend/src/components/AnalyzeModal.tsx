"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useStore } from "@/lib/store";
import type { AnalyzeResponse } from "@/lib/types";

const CLASSIFICATION_STYLE: Record<string, string> = {
  pozitif: "text-emerald-400",
  negatif: "text-red-400",
  nötr: "text-zinc-400",
};

export default function AnalyzeModal({ symbol, onClose }: { symbol: string; onClose: () => void }) {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const upsertCard = useStore((s) => s.upsertCard);
  const addToast = useStore((s) => s.addToast);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .analyzeSymbol(symbol)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol]);

  async function handleAccept() {
    if (!result?.card_draft) return;
    setAccepting(true);
    try {
      const card = await api.acceptCardDraft(symbol, result.card_draft);
      upsertCard(card);
      addToast(`${symbol} kartı aktif edildi`, "win");
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "kart kabul edilemedi");
    } finally {
      setAccepting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{symbol} — Manuel Analiz</h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-zinc-100">
            ✕
          </button>
        </div>

        {loading && <p className="text-zinc-400">Analiz ediliyor...</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}

        {result && !loading && (
          <div className="space-y-4">
            <div
              className={`rounded-lg border px-3 py-2 text-sm ${
                result.verdict === "setup"
                  ? "border-emerald-800 bg-emerald-950/40 text-emerald-300"
                  : "border-zinc-700 bg-zinc-800/60 text-zinc-300"
              }`}
            >
              {result.verdict === "setup" ? "✅ Setup bulundu" : "⊘ Setup yok"}
              {result.skip_reason && <p className="mt-1 text-zinc-400">{result.skip_reason}</p>}
            </div>

            {result.context_summary && (
              <div className="space-y-2 text-sm">
                <div className="grid grid-cols-2 gap-2">
                  <div>Fiyat: ${result.context_summary.price.toFixed(2)}</div>
                  <div>RVOL: {result.context_summary.rvol.toFixed(1)}x</div>
                  <div>ATR: {result.context_summary.atr.toFixed(2)}</div>
                  <div>
                    S/R: {result.context_summary.key_levels.support ?? "-"} /{" "}
                    {result.context_summary.key_levels.resistance ?? "-"}
                  </div>
                </div>
                {result.context_summary.warnings.length > 0 && (
                  <ul className="space-y-0.5 text-xs text-amber-400">
                    {result.context_summary.warnings.map((w, i) => (
                      <li key={i}>⚠️ {w}</li>
                    ))}
                  </ul>
                )}
                {result.context_summary.news.length > 0 && (
                  <div>
                    <h3 className="mb-1 text-xs font-medium text-zinc-400">Haberler</h3>
                    <ul className="space-y-1 text-xs">
                      {result.context_summary.news.map((n, i) => (
                        <li key={i}>
                          <span className={CLASSIFICATION_STYLE[n.classification] || "text-zinc-400"}>
                            [{n.classification}]
                          </span>{" "}
                          {n.headline} — {n.source}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {result.card_draft && (
              <div className="rounded-lg border border-sky-800 bg-sky-950/30 p-3 text-sm">
                <span className="mb-2 inline-block rounded bg-sky-500/20 px-1.5 py-0.5 text-xs text-sky-300">
                  TASLAK
                </span>
                <div className="grid grid-cols-2 gap-1">
                  <div>Giriş: {result.card_draft.entry_zone_low}–{result.card_draft.entry_zone_high}</div>
                  <div>Stop: {result.card_draft.stop}</div>
                  <div>T1: {result.card_draft.target_1}</div>
                  <div>T2: {result.card_draft.target_2}</div>
                  <div>Vade: {result.card_draft.horizon}</div>
                  <div>Güven: {result.card_draft.confidence}</div>
                </div>
                {result.card_draft.reasoning && (
                  <p className="mt-2 text-zinc-300">💡 {result.card_draft.reasoning}</p>
                )}
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={handleAccept}
                    disabled={accepting}
                    className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium hover:bg-emerald-500 disabled:opacity-50"
                  >
                    {accepting ? "Kaydediliyor..." : "Kartı Kabul Et"}
                  </button>
                  <button
                    onClick={onClose}
                    className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs hover:bg-zinc-800"
                  >
                    Vazgeç
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
