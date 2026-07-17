"use client";

import { useStore } from "@/lib/store";
import EquityCurve from "./EquityCurve";

export default function StatsPanel() {
  const stats = useStore((s) => s.stats);
  const settings = useStore((s) => s.settings);

  if (!stats) return <p className="text-sm text-zinc-500">İstatistik yükleniyor...</p>;

  const resolvedCount = stats.wins + stats.losses + stats.expired + stats.no_fill;
  const paperMode = settings?.paper_mode ?? true;

  return (
    <div className="space-y-4">
      {paperMode && (
        <div className="rounded-lg border border-amber-800 bg-amber-950/40 px-3 py-2 text-sm text-amber-300">
          📝 Kağıt modundasın — {Math.max(0, 50 - resolvedCount)} kart sonra gerçek istatistiğin
          oluşacak
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Win Rate" value={`%${(stats.win_rate * 100).toFixed(0)}`} />
        <Stat label="Toplam R" value={stats.total_r.toFixed(1)} />
        <Stat label="Ort. R" value={stats.avg_r.toFixed(2)} />
        <Stat label="Toplam Kart" value={String(stats.total)} />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-zinc-300">Vadeye Göre</h3>
        <div className="space-y-1">
          {Object.entries(stats.by_horizon).map(([horizon, h]) => (
            <div key={horizon} className="flex justify-between rounded bg-zinc-900 px-3 py-1.5 text-sm">
              <span>{horizon}</span>
              <span className="text-zinc-400">
                {h.wins}/{h.count} · {h.total_r.toFixed(1)}R
              </span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-zinc-300">Kümülatif R Eğrisi</h3>
        <EquityCurve />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
