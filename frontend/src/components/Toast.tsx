"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useStore } from "@/lib/store";

const KIND_STYLE: Record<string, string> = {
  win: "border-emerald-700 bg-emerald-950/80 text-emerald-300",
  loss: "border-red-700 bg-red-950/80 text-red-300",
  info: "border-zinc-700 bg-zinc-900/90 text-zinc-200",
};

export default function Toast() {
  const toasts = useStore((s) => s.toasts);
  const removeToast = useStore((s) => s.removeToast);

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-30 flex w-72 flex-col gap-2">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            onClick={() => removeToast(t.id)}
            className={`pointer-events-auto cursor-pointer rounded-lg border px-3 py-2 text-sm shadow-lg ${KIND_STYLE[t.kind]}`}
          >
            {t.message}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
