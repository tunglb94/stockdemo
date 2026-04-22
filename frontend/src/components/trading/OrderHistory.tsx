"use client";
import { useState } from "react";
import toast from "react-hot-toast";
import { Order } from "@/types/trading";
import { tradingService } from "@/services/tradingService";
import { formatCurrency, formatDate } from "@/utils/formatters";
import { STATUS_LABELS, STATUS_COLORS } from "@/utils/constants";

interface Props {
  orders: Order[];
  onCancelled?: (id: string) => void;
}

export default function OrderHistory({ orders, onCancelled }: Props) {
  const [cancelling, setCancelling] = useState<string | null>(null);

  async function handleCancel(order: Order) {
    setCancelling(order.id);
    try {
      await tradingService.cancelOrder(order.id);
      toast.success("Hủy lệnh thành công.");
      onCancelled?.(order.id);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || "Hủy lệnh thất bại.";
      toast.error(msg);
    } finally {
      setCancelling(null);
    }
  }

  if (!orders.length) {
    return (
      <div className="bg-dark-surface border border-dark-border rounded-xl p-8 text-center text-gray-500">
        Chưa có lệnh nào.
      </div>
    );
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-dark-border text-gray-400 text-xs">
            <th className="px-4 py-3 text-left">Mã CK</th>
            <th className="px-4 py-3 text-center">Loại</th>
            <th className="px-4 py-3 text-center">Hướng</th>
            <th className="px-4 py-3 text-right">KL đặt</th>
            <th className="px-4 py-3 text-right">Giá đặt</th>
            <th className="px-4 py-3 text-right">KL khớp</th>
            <th className="px-4 py-3 text-right">Giá khớp</th>
            <th className="px-4 py-3 text-center">Trạng thái</th>
            <th className="px-4 py-3 text-left">Thời gian</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id} className="border-b border-dark-border/50 hover:bg-dark-bg/30">
              <td className="px-4 py-3 font-semibold text-white">{order.stock_symbol}</td>
              <td className="px-4 py-3 text-center text-gray-400">{order.order_type}</td>
              <td className={`px-4 py-3 text-center font-semibold ${
                order.side === "BUY" ? "text-price-up" : "text-price-down"
              }`}>
                {order.side === "BUY" ? "MUA" : "BÁN"}
              </td>
              <td className="px-4 py-3 text-right text-gray-300">{order.quantity.toLocaleString()}</td>
              <td className="px-4 py-3 text-right text-gray-300">
                {order.price ? (order.price / 1000).toFixed(2) : "—"}
              </td>
              <td className="px-4 py-3 text-right text-gray-300">{order.matched_quantity.toLocaleString()}</td>
              <td className="px-4 py-3 text-right text-gray-300">
                {order.matched_price ? (order.matched_price / 1000).toFixed(2) : "—"}
              </td>
              <td className="px-4 py-3 text-center">
                <span className={`text-xs px-2 py-1 rounded-full ${STATUS_COLORS[order.status] || ""}`}>
                  {STATUS_LABELS[order.status] || order.status}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                {formatDate(order.created_at)}
              </td>
              <td className="px-4 py-3 text-right">
                {(order.status === "PENDING" || order.status === "PARTIAL") && (
                  <button
                    onClick={() => handleCancel(order)}
                    disabled={cancelling === order.id}
                    className="text-xs text-red-400 hover:text-red-300 disabled:opacity-50 transition"
                  >
                    {cancelling === order.id ? "..." : "Hủy"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
