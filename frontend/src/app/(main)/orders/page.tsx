"use client";
import { useEffect, useState } from "react";
import { tradingService } from "@/services/tradingService";
import { Order } from "@/types/trading";
import OrderHistory from "@/components/trading/OrderHistory";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"ALL" | "PENDING" | "MATCHED" | "CANCELLED">("ALL");

  useEffect(() => {
    tradingService.getOrders(filter !== "ALL" ? { status: filter } : undefined)
      .then(setOrders)
      .finally(() => setLoading(false));
  }, [filter]);

  const tabs: Array<typeof filter> = ["ALL", "PENDING", "MATCHED", "CANCELLED"];
  const tabLabels: Record<typeof filter, string> = {
    ALL: "Tất cả", PENDING: "Chờ khớp", MATCHED: "Đã khớp", CANCELLED: "Đã hủy",
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Lịch sử lệnh</h1>

      <div className="flex gap-2">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2 rounded-lg text-sm transition ${
              filter === tab
                ? "bg-price-up text-white"
                : "border border-dark-border text-gray-400 hover:border-gray-500"
            }`}
          >
            {tabLabels[tab]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400">Đang tải...</div>
      ) : (
        <OrderHistory orders={orders} onCancelled={(id) =>
          setOrders((prev) => prev.map((o) => o.id === id ? { ...o, status: "CANCELLED" } : o))
        } />
      )}
    </div>
  );
}
