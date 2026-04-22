"use client";
import StockBoard from "@/components/market/StockBoard";
import { useMarketData } from "@/hooks/useMarketData";

export default function MarketPage() {
  const { stocks, lastUpdated, refetch } = useMarketData(60_000);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Bảng giá VN30</h1>
          {lastUpdated && (
            <p className="text-gray-500 text-xs mt-1">
              Cập nhật lúc {lastUpdated.toLocaleTimeString("vi-VN")}
            </p>
          )}
        </div>
        <button
          onClick={refetch}
          className="text-sm text-gray-400 border border-dark-border rounded-lg px-4 py-2 hover:border-gray-500 transition"
        >
          Làm mới
        </button>
      </div>

      <StockBoard stocks={stocks} />
    </div>
  );
}
