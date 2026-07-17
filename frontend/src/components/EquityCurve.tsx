"use client";

import { useMemo } from "react";
import { useStore } from "@/lib/store";

export default function EquityCurve() {
  const cards = useStore((s) => s.cards);

  const points = useMemo(() => {
    const resolved = cards
      .filter((c) => c.realized_r != null)
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    let cumulative = 0;
    return resolved.map((c) => {
      cumulative += c.realized_r ?? 0;
      return cumulative;
    });
  }, [cards]);

  if (points.length < 2) {
    return <p className="text-sm text-zinc-500">Eğri için yeterli kapanmış kart yok.</p>;
  }

  const width = 600;
  const height = 160;
  const max = Math.max(...points, 0);
  const min = Math.min(...points, 0);
  const range = max - min || 1;

  const path = points
    .map((v, i) => {
      const x = (i / (points.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const zeroY = height - ((0 - min) / range) * height;
  const last = points[points.length - 1];

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="none">
        <line x1={0} y1={zeroY} x2={width} y2={zeroY} stroke="#3f3f46" strokeDasharray="4 4" />
        <path d={path} fill="none" stroke={last >= 0 ? "#34d399" : "#f87171"} strokeWidth={2} />
      </svg>
      <p className="mt-1 text-xs text-zinc-500">Kümülatif R: {last.toFixed(2)}</p>
    </div>
  );
}
