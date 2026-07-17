"use client";

import { useEffect, useRef } from "react";
import { useStore } from "@/lib/store";
import type { PriceTick, TradeCard, WSMessage } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
const RECONNECT_DELAY_MS = 3000;
const MAX_FAILS_BEFORE_BANNER = 5;

export function useWebSocket() {
  const failCountRef = useRef(0);
  const upsertCard = useStore((s) => s.upsertCard);
  const applyTicks = useStore((s) => s.applyTicks);
  const setWsStatus = useStore((s) => s.setWsStatus);
  const addToast = useStore((s) => s.addToast);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      setWsStatus("connecting");
      socket = new WebSocket(`${WS_URL}/ws/live`);

      socket.onopen = () => {
        failCountRef.current = 0;
        setWsStatus("open");
      };

      socket.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          handleMessage(msg, { upsertCard, applyTicks, addToast });
        } catch {
          // yoksayılan mesaj
        }
      };

      socket.onclose = () => {
        setWsStatus("closed");
        failCountRef.current += 1;
        if (failCountRef.current >= MAX_FAILS_BEFORE_BANNER) {
          addToast("Canlı bağlantı kurulamıyor, tekrar deneniyor...", "info");
        }
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      };

      socket.onerror = () => {
        socket?.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

function handleMessage(
  msg: WSMessage,
  actions: {
    upsertCard: (card: TradeCard) => void;
    applyTicks: (ticks: PriceTick[]) => void;
    addToast: (message: string, kind: "win" | "loss" | "info") => void;
  }
) {
  switch (msg.type) {
    case "card_created": {
      const card = msg.data as TradeCard;
      actions.upsertCard(card);
      actions.addToast(`Yeni kart: ${card.symbol}`, "info");
      break;
    }
    case "card_updated": {
      const card = msg.data as TradeCard;
      actions.upsertCard(card);
      if (card.status === "TARGET_HIT") {
        actions.addToast(`${card.symbol} hedefe ulaştı (+${card.realized_r}R)`, "win");
      } else if (card.status === "STOP_HIT") {
        actions.addToast(`${card.symbol} stop oldu (${card.realized_r}R)`, "loss");
      } else if (card.status === "EXPIRED") {
        actions.addToast(`${card.symbol} vadesi doldu`, "info");
      }
      break;
    }
    case "price_tick": {
      const data = msg.data as { cards: PriceTick[] };
      actions.applyTicks(data.cards);
      break;
    }
    case "scan_completed":
      break;
  }
}
