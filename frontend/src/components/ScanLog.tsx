"use client";

import { useStore } from "@/lib/store";

export default function ScanLog() {
  const scanRuns = useStore((s) => s.scanRuns);

  if (scanRuns.length === 0) return <p className="text-sm text-zinc-500">Henüz tarama yapılmadı.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs text-zinc-500">
          <tr>
            <th className="px-2 py-1">Zaman</th>
            <th className="px-2 py-1">Evren</th>
            <th className="px-2 py-1">Ön Filtre</th>
            <th className="px-2 py-1">Gemini</th>
            <th className="px-2 py-1">Kart</th>
            <th className="px-2 py-1">Red</th>
            <th className="px-2 py-1">Süre</th>
          </tr>
        </thead>
        <tbody>
          {scanRuns.map((run) => (
            <tr key={run.id} className="border-t border-zinc-800">
              <td className="px-2 py-1">{new Date(run.ran_at).toLocaleTimeString("tr-TR")}</td>
              <td className="px-2 py-1">{run.universe_size}</td>
              <td className="px-2 py-1">{run.prefiltered_count}</td>
              <td className="px-2 py-1">{run.gemini_calls}</td>
              <td className="px-2 py-1 text-emerald-400">{run.cards_created}</td>
              <td className="px-2 py-1 text-zinc-500">{run.cards_rejected}</td>
              <td className="px-2 py-1">{run.duration_ms}ms</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
