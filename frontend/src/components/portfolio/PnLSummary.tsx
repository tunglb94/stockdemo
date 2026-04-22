"use client";
import { PortfolioSummary } from "@/types/trading";
import { formatCurrency, formatPercent } from "@/utils/formatters";

interface Props {
  summary: PortfolioSummary;
}

export default function PnLSummary({ summary }: Props) {
  const isProfit = summary.total_pnl >= 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
        <p className="text-xs text-gray-500 mb-2">Tổng tài sản</p>
        <p className="text-xl font-bold text-white">{formatCurrency(Math.round(summary.total_assets))}</p>
        <p className="text-xs text-gray-500 mt-1">VNĐ</p>
      </div>

      <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
        <p className="text-xs text-gray-500 mb-2">Tiền mặt khả dụng</p>
        <p className="text-xl font-bold text-white">{formatCurrency(Math.round(summary.wallet.available_balance))}</p>
        {summary.wallet.frozen_balance > 0 && (
          <p className="text-xs text-gray-600 mt-1">
            +{formatCurrency(Math.round(summary.wallet.frozen_balance))} đang giam
          </p>
        )}
      </div>

      <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
        <p className="text-xs text-gray-500 mb-2">Giá trị danh mục</p>
        <p className="text-xl font-bold text-white">{formatCurrency(Math.round(summary.total_market_value))}</p>
        <p className="text-xs text-gray-500 mt-1">Giá vốn: {formatCurrency(Math.round(summary.total_cost))}</p>
      </div>

      <div className={`bg-dark-surface border rounded-xl p-5 ${
        isProfit ? "border-price-up/20" : "border-price-down/20"
      }`}>
        <p className="text-xs text-gray-500 mb-2">Lãi / Lỗ chưa thực hiện</p>
        <p className={`text-xl font-bold ${isProfit ? "text-price-up" : "text-price-down"}`}>
          {isProfit ? "+" : ""}{formatCurrency(Math.round(summary.total_pnl))}
        </p>
        <p className={`text-sm mt-1 ${isProfit ? "text-price-up" : "text-price-down"}`}>
          {formatPercent(summary.total_pnl_percent)}
        </p>
      </div>
    </div>
  );
}
