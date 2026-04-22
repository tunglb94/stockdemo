"use client";
import { useEffect, useCallback } from "react";
import { useMarketStore } from "@/store/marketStore";
import { marketService } from "@/services/marketService";

export function useMarketData(intervalMs = 60_000) {
  const { stocks, setStocks, lastUpdated } = useMarketStore();

  const fetchData = useCallback(async () => {
    try {
      const data = await marketService.getStocks(true);
      setStocks(data);
    } catch (err) {
      console.error("Lỗi fetch market data:", err);
    }
  }, [setStocks]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, intervalMs);
    return () => clearInterval(interval);
  }, [fetchData, intervalMs]);

  return { stocks, lastUpdated, refetch: fetchData };
}

export function useStockWebSocket(symbol: string, onUpdate: (data: unknown) => void) {
  useEffect(() => {
    if (!symbol) return;
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/market/${symbol}/`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "price_update") {
          onUpdate(msg.data);
        }
      } catch {}
    };

    ws.onerror = () => console.warn(`WS lỗi: ${symbol}`);

    return () => ws.close();
  }, [symbol, onUpdate]);
}
