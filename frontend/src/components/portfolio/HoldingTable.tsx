"use client";
import Link from "next/link";
import { Holding } from "@/types/trading";
import { formatCurrency, formatPercent } from "@/utils/formatters";

interface Props {
  holdings: Holding[];
}

export default function HoldingTable({ holdings }: Props) {
  if (!holdings.length) {
    return (
      <div className="bg-dark-surface border border-dark-border rounded-xl p-8 text-center text-gray-500">
        Bạn chưa nắm giữ cổ phiếu nào.
      </div>
    );
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-dark-border">
        <h2 className="text-sm font-semibold text-white">Cổ phiếu đang nắm giữ</h2>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-dark-border text-gray-400 text-xs">
            <th className="px-4 py-3 text-left">Mã CK</th>
            <th className="px-4 py-3 text-right">SL</th>
            <th className="px-4 py-3 text-right">Có thể bán</th>
            <th className="px-4 py-3 text-right">Giá vốn TB</th>
            <th className="px-4 py-3 text-right">Giá hiện tại</th>
            <th className="px-4 py-3 text-right">Giá trị TT</th>
            <th className="px-4 py-3 text-right">Lãi / Lỗ</th>
            <th className="px-4 py-3 text-right">%</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {holdings.map((h) => {
            const pnlPercent = h.avg_cost > 0
              ? ((h.market_value - h.avg_cost * h.quantity) / (h.avg_cost * h.quantity)) * 100
              : 0;
            const isProfit = h.unrealized_pnl >= 0;

            return (
              <tr key={h.symbol} className="border-b border-dark-border/50 hover:bg-dark-bg/30">
                <td className="px-4 py-3">
                  <Link href={`/market/${h.symbol}`} className="font-semibold text-white hover:text-price-up">
                    {h.symbol}
                  </Link>
                  <div className="text-xs text-gray-500 truncate max-w-[120px]">{h.company_name}</div>
                </td>
                <td className="px-4 py-3 text-right text-gray-300">{h.quantity.toLocaleString()}</td>
                <td className="px-4 py-3 text-right">
                  <span className={h.available_quantity > 0 ? "text-price-up" : "text-gray-500"}>
                    {h.available_quantity.toLocaleString()}
                  </span>
                  {h.frozen_quantity > 0 && (
                    <span className="text-gray-500 text-xs ml-1">(+{h.frozen_quantity} giam)</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-gray-300">{(h.avg_cost / 1000).toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-gray-300">
                  {h.market_value > 0 ? (h.market_value / h.quantity / 1000).toFixed(2) : "—"}
                </td>
                <td className="px-4 py-3 text-right text-white">{formatCurrency(Math.round(h.market_value))}</td>
                <td className={`px-4 py-3 text-right font-semibold ${isProfit ? "text-price-up" : "text-price-down"}`}>
                  {isProfit ? "+" : ""}{formatCurrency(Math.round(h.unrealized_pnl))}
                </td>
                <td className={`px-4 py-3 text-right ${isProfit ? "text-price-up" : "text-price-down"}`}>
                  {formatPercent(pnlPercent)}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/market/${h.symbol}`}
                    className="text-xs text-gray-500 hover:text-white transition"
                  >
                    Giao dịch
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
