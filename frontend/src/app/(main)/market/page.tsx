"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import { useMarketStore } from "@/store/marketStore";
import { marketService } from "@/services/marketService";
import StockBoard from "@/components/market/StockBoard";
import { Stock } from "@/types/market";

type Tab = "VN30" | "HOSE" | "HNX" | "UPCOM";
const TABS: Tab[] = ["VN30", "HOSE", "HNX", "UPCOM"];
const REFRESH_MS: Record<Tab, number> = { VN30: 15_000, HOSE: 30_000, HNX: 30_000, UPCOM: 60_000 };

export default function MarketPage() {
  const { setStocks, lastUpdated } = useMarketStore();
  const [tab, setTab] = useState<Tab>("VN30");
  const [search, setSearch] = useState("");
  const [displayStocks, setDisplayStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchStocks = useCallback(async (t: Tab, q: string) => {
    try {
      const params: Record<string, string> = {};
      if (t === "VN30") params.vn30 = "1";
      else params.exchange = t;
      if (q) params.q = q;
      const data = await marketService.getStocksRaw(params);
      setDisplayStocks(data);
      if (t === "VN30") setStocks(data);
    } catch (err) {
      console.error("Lỗi fetch:", err);
    } finally {
      setLoading(false);
    }
  }, [setStocks]);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setLoading(true);
    fetchStocks(tab, search);
    const schedule = () => {
      timerRef.current = setTimeout(() => { fetchStocks(tab, search); schedule(); }, REFRESH_MS[tab]);
    };
    schedule();
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [tab, search, fetchStocks]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-dark-border bg-dark-surface shrink-0">
        <div className="flex gap-0.5">
          {TABS.map(t => (
            <button key={t} onClick={() => { setTab(t); setSearch(""); }}
              className={`px-3 py-1 text-xs font-medium rounded transition ${
                tab === t ? "bg-price-up/20 text-price-up border border-price-up/30"
                          : "text-gray-500 hover:text-white hover:bg-dark-bg"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <input
            type="text" placeholder="Tìm mã..." value={search}
            onChange={e => setSearch(e.target.value.toUpperCase())}
            className="bg-dark-bg border border-dark-border rounded px-2 py-1 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500 w-28"
          />
          <span className="text-gray-600 text-xs tabular-nums">
            {displayStocks.length} mã{lastUpdated && ` · ${lastUpdated.toLocaleTimeString("vi-VN")}`}
          </span>
          <button onClick={() => fetchStocks(tab, search)}
            className="text-xs text-gray-500 hover:text-white border border-dark-border rounded px-2 py-1 transition">
            ↻
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {loading && displayStocks.length === 0
          ? <div className="flex items-center justify-center h-32 text-gray-600 text-sm">Đang tải...</div>
          : <StockBoard stocks={displayStocks} />
        }
      </div>
    </div>
  );
}
