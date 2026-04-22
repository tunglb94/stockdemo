"use client";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { tradingService } from "@/services/tradingService";
import { PortfolioSummary } from "@/types/trading";
import { formatCurrency, formatPercent } from "@/utils/formatters";
import PnLSummary from "@/components/portfolio/PnLSummary";
import HoldingTable from "@/components/portfolio/HoldingTable";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    tradingService.getPortfolio()
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400 p-4">Đang tải danh mục...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Xin chào, {user?.username}</h1>
        <p className="text-gray-500 text-sm mt-1">Tổng quan tài khoản giao dịch của bạn</p>
      </div>

      {/* Thẻ tổng quan */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: "Tổng tài sản",
            value: formatCurrency(summary?.total_assets),
            sub: "VNĐ",
            color: "text-white",
          },
          {
            label: "Tiền mặt khả dụng",
            value: formatCurrency(summary?.wallet.available_balance),
            sub: "VNĐ",
            color: "text-white",
          },
          {
            label: "Giá trị cổ phiếu",
            value: formatCurrency(summary?.total_market_value),
            sub: "VNĐ",
            color: "text-white",
          },
          {
            label: "Lãi / Lỗ chưa thực hiện",
            value: formatCurrency(summary?.total_pnl),
            sub: formatPercent(summary?.total_pnl_percent),
            color:
              (summary?.total_pnl ?? 0) >= 0 ? "text-price-up" : "text-price-down",
          },
        ].map((card) => (
          <div key={card.label} className="bg-dark-surface border border-dark-border rounded-xl p-4">
            <p className="text-gray-500 text-xs mb-2">{card.label}</p>
            <p className={`text-lg font-bold ${card.color}`}>{card.value}</p>
            <p className="text-gray-400 text-xs mt-1">{card.sub}</p>
          </div>
        ))}
      </div>

      {summary && <HoldingTable holdings={summary.holdings} />}
    </div>
  );
}
