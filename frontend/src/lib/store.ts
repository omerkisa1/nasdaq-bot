import { create } from "zustand";
import type { Health, PriceTick, ScanRun, Settings, Stats, TradeCard } from "./types";

export interface ToastItem {
  id: number;
  message: string;
  kind: "win" | "loss" | "info";
}

let toastCounter = 0;

interface StoreState {
  cards: TradeCard[];
  stats: Stats | null;
  settings: Settings | null;
  scanRuns: ScanRun[];
  health: Health | null;
  wsStatus: "connecting" | "open" | "closed";
  toasts: ToastItem[];

  setCards: (cards: TradeCard[]) => void;
  upsertCard: (card: TradeCard) => void;
  applyTicks: (ticks: PriceTick[]) => void;
  setStats: (stats: Stats) => void;
  setSettings: (settings: Settings) => void;
  setScanRuns: (runs: ScanRun[]) => void;
  setHealth: (health: Health) => void;
  setWsStatus: (status: StoreState["wsStatus"]) => void;
  addToast: (message: string, kind: ToastItem["kind"]) => void;
  removeToast: (id: number) => void;
}

export const useStore = create<StoreState>((set, get) => ({
  cards: [],
  stats: null,
  settings: null,
  scanRuns: [],
  health: null,
  wsStatus: "connecting",
  toasts: [],

  setCards: (cards) => set({ cards }),

  upsertCard: (card) =>
    set((state) => {
      const exists = state.cards.some((c) => c.id === card.id);
      const cards = exists
        ? state.cards.map((c) => (c.id === card.id ? { ...c, ...card } : c))
        : [card, ...state.cards];
      return { cards };
    }),

  applyTicks: (ticks) =>
    set((state) => {
      const byId = new Map(ticks.map((t) => [t.id, t]));
      return {
        cards: state.cards.map((c) => {
          const tick = byId.get(c.id);
          if (!tick) return c;
          return {
            ...c,
            current_price: tick.price,
            pct_to_target: tick.pct_to_target,
            pct_to_stop: tick.pct_to_stop,
          };
        }),
      };
    }),

  setStats: (stats) => set({ stats }),
  setSettings: (settings) => set({ settings }),
  setScanRuns: (scanRuns) => set({ scanRuns }),
  setHealth: (health) => set({ health }),
  setWsStatus: (wsStatus) => set({ wsStatus }),

  addToast: (message, kind) => {
    const id = ++toastCounter;
    set((state) => ({ toasts: [...state.toasts, { id, message, kind }] }));
    setTimeout(() => get().removeToast(id), 5000);
  },
  removeToast: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
