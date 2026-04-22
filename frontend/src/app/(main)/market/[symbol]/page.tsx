"use client";
import { useEffect, useState } from "react";
import { use } from "react";
import { marketService } from "@/services/marketService";
import { Stock } from "@/types/market";
import StockChart from "@/components/market/StockChart";
import OrderForm from "@/components/trading/OrderForm";
import { formatCurrency, formatPercent } from "@/utils/formatters";
import { getPriceColor, getPriceColorClass } from "@/utils/calculators";

export default function StockDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = use(params);
  const [stock, setStock] = useState<Stock | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sym = symbol.toUpperCase();
    marketService.getStock(sym)
      .then(setStock)
      .catch(console.error)
      .finally(() => setLoading(false));

    const interval = setInterval(() => {
      marketService.getStock(sym).then(setStock).catch(() => {});
    }, 30_000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (loading) return <div className="text-gray-400 p-4">Đang tải {symbol.toUpperCase()}...</div>;
  if (!stock) return <div className="text-red-400 p-4">Không tìm thấy mã {symbol.toUpperCase()}</div>;

  const snap = stock.latest_price;
  const color = snap ? getPriceColor(snap.current_price, snap) : "ref";
  const colorClass = getPriceColorClass(color);

  return (
    <div className="space-y-4">
      {/* Header mã CK */}
      <div className="bg-dark-surface border border-dark-border rounded-xl p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-white">{stock.symbol}</h1>
              <span className="text-xs bg-dark-bg border border-dark-border rounded px-2 py-1 text-gray-400">
                {stock.exchange}
              </span>
            </div>
            <p className="text-gray-400 mt-1">{stock.company_name}</p>
          </div>

          {snap && (
            <div className="text-right">
              <div className={`text-4xl font-bold ${colorClass}`}>
                {(snap.current_price / 1000).toFixed(2)}
              </div>
              <div className={`text-sm mt-1 ${colorClass}`}>
                {snap.change >= 0 ? "+" : ""}{(snap.change / 1000).toFixed(2)} ({formatPercent(snap.change_percent)})
              </div>
            </div>
          )}
        </div>

        {snap && (
          <div className="grid grid-cols-3 lg:grid-cols-6 gap-4 mt-6 pt-4 border-t border-dark-border">
            {[
              { label: "Tham chiếu", value: (snap.reference_price / 1000).toFixed(2), color: "text-price-ref" },
              { label: "Trần", value: (snap.ceiling_price / 1000).toFixed(2), color: "text-price-ceiling" },
              { label: "Sàn", value: (snap.floor_price / 1000).toFixed(2), color: "text-price-floor" },
              { label: "Cao nhất", value: snap.high_price ? (snap.high_price / 1000).toFixed(2) : "—", color: "text-price-up" },
              { label: "Thấp nhất", value: snap.low_price ? (snap.low_price / 1000).toFixed(2) : "—", color: "text-price-down" },
              { label: "KLGD", value: formatCurrency(snap.volume), color: "text-white" },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-xs text-gray-500">{item.label}</p>
                <p className={`font-semibold mt-1 ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Biểu đồ + Form đặt lệnh */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <StockChart symbol={stock.symbol} />
        </div>
        <div>
          <OrderForm stock={stock} />
        </div>
      </div>
    </div>
  );
}
