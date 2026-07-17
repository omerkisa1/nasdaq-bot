"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";

export default function SettingsPanel() {
  const settings = useStore((s) => s.settings);
  const setSettings = useStore((s) => s.setSettings);
  const [saving, setSaving] = useState(false);

  if (!settings) return <p className="text-sm text-zinc-500">Ayarlar yükleniyor...</p>;

  async function save(patch: Record<string, unknown>) {
    setSaving(true);
    try {
      const updated = await api.patchSettings(patch);
      setSettings(updated);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-md space-y-4 text-sm">
      <Field
        label="Hesap büyüklüğü ($)"
        type="number"
        value={settings.account_size}
        onSave={(v) => save({ account_size: Number(v) })}
      />
      <Field
        label="Risk yüzdesi (%)"
        type="number"
        value={settings.risk_percent}
        onSave={(v) => save({ risk_percent: Number(v) })}
      />
      <Field
        label="Maksimum aktif kart"
        type="number"
        value={settings.max_active_cards}
        onSave={(v) => save({ max_active_cards: Number(v) })}
      />
      <Field
        label="Min güven eşiği"
        type="number"
        value={settings.min_confidence}
        onSave={(v) => save({ min_confidence: Number(v) })}
      />

      <label className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2">
        <span>Tarama aktif</span>
        <input
          type="checkbox"
          checked={Boolean(settings.scan_enabled)}
          onChange={(e) => save({ scan_enabled: e.target.checked })}
        />
      </label>

      <label className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2">
        <span>Kağıt modu (paper mode)</span>
        <input
          type="checkbox"
          checked={Boolean(settings.paper_mode)}
          onChange={(e) => save({ paper_mode: e.target.checked })}
        />
      </label>

      {saving && <p className="text-xs text-zinc-500">Kaydediliyor...</p>}
    </div>
  );
}

function Field({
  label,
  type,
  value,
  onSave,
}: {
  label: string;
  type: string;
  value: number;
  onSave: (v: string) => void;
}) {
  const [local, setLocal] = useState(String(value));
  return (
    <label className="block">
      <span className="mb-1 block text-zinc-400">{label}</span>
      <input
        type={type}
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        onBlur={() => local !== String(value) && onSave(local)}
        className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1.5"
      />
    </label>
  );
}
