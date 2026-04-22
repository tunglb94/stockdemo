"use client";
import { useState } from "react";
import toast from "react-hot-toast";
import { Stock } from "@/types/market";
import { OrderSide, OrderType } from "@/types/trading";
import { tradingService } from "@/services/tradingService";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, formatPercent } from "@/utils/formatters";
import { calcTradingFee, calcSellTax } from "@/utils/calculators";
import { ORDER_TYPES } from "@/utils/constants";

interface Props {
  stock: Stock;
}

export default function OrderForm({ stock }: Props) {
  const { user } = useAuthStore();
  const snap = stock.latest_price;

  const [side, setSide] = useState<OrderSide>("BUY");
  const [orderType, setOrderType] = useState<OrderType>("LO");
  const [quantity, setQuantity] = useState<number>(100);
  const [price, setPrice] = useState<number>(snap?.current_price ?? 0);
  const [loading, setLoading] = useState(false);

  const currentPrice = snap?.current_price ?? 0;
  const displayPrice = (currentPrice / 1000).toFixed(2);
  const total = price * quantity;
  const fee = calcTradingFee(price, quantity);
  const tax = side === "SELL" ? calcSellTax(price, quantity) : 0;
  const netTotal = side === "BUY" ? total + fee : total - fee - tax;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (quantity % 100 !== 0) {
      toast.error("Khối lượng phải là bội số của 100 (1 lô = 100 cổ phiếu).");
      return;
    }
    setLoading(true);
    try {
      const res = await tradingService.placeOrder({
        symbol: stock.symbol,
        side,
        order_type: orderType,
        quantity,
        price: orderType === "LO" ? price : null,
      });
      toast.success(`${res.message} — Trạng thái: ${res.order.status === "MATCHED" ? "Đã khớp" : "Chờ khớp"}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || "Đặt lệnh thất bại.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
      {/* Tab MUA / BÁN */}
      <div className="grid grid-cols-2">
        {(["BUY", "SELL"] as OrderSide[]).map((s) => (
          <button
            key={s}
            onClick={() => setSide(s)}
            className={`py-3 text-sm font-semibold transition ${
              side === s
                ? s === "BUY"
                  ? "bg-price-up text-white"
                  : "bg-price-down text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {s === "BUY" ? "MUA" : "BÁN"}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="p-4 space-y-4">
        {/* Giá hiện tại */}
        <div className="bg-dark-bg rounded-lg p-3 text-center">
          <div className="text-xs text-gray-500 mb-1">Giá hiện tại</div>
          <div className={`text-2xl font-bold ${
            (snap?.change ?? 0) >= 0 ? "text-price-up" : "text-price-down"
          }`}>
            {displayPrice}
          </div>
          {snap && (
            <div className="text-xs text-gray-500 mt-1">
              {snap.change >= 0 ? "+" : ""}{(snap.change / 1000).toFixed(2)} ({formatPercent(snap.change_percent)})
            </div>
          )}
        </div>

        {/* Loại lệnh */}
        <div>
          <label className="text-xs text-gray-500 block mb-1.5">Loại lệnh</label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as OrderType)}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-price-up"
          >
            {ORDER_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* Giá (chỉ hiện khi LO) */}
        {orderType === "LO" && (
          <div>
            <label className="text-xs text-gray-500 block mb-1.5">
              Giá đặt (nghìn đồng)
              {snap && (
                <span className="ml-2 text-gray-600">
                  [{(snap.floor_price / 1000).toFixed(2)} — {(snap.ceiling_price / 1000).toFixed(2)}]
                </span>
              )}
            </label>
            <input
              type="number"
              step="0.1"
              min={snap ? snap.floor_price / 1000 : 0}
              max={snap ? snap.ceiling_price / 1000 : 99999}
              value={price / 1000}
              onChange={(e) => setPrice(parseFloat(e.target.value) * 1000)}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-price-up"
            />
          </div>
        )}

        {/* Khối lượng */}
        <div>
          <label className="text-xs text-gray-500 block mb-1.5">Khối lượng (bội số 100)</label>
          <input
            type="number"
            step={100}
            min={100}
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value))}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-price-up"
          />
          <div className="flex gap-2 mt-2">
            {[100, 500, 1000, 5000].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuantity(q)}
                className="flex-1 text-xs py-1 border border-dark-border rounded text-gray-400 hover:border-gray-500 transition"
              >
                {q >= 1000 ? `${q / 1000}K` : q}
              </button>
            ))}
          </div>
        </div>

        {/* Tóm tắt */}
        <div className="bg-dark-bg rounded-lg p-3 space-y-2 text-sm">
          <div className="flex justify-between text-gray-400">
            <span>Giá trị lệnh</span>
            <span className="text-white">{formatCurrency(total)} VNĐ</span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Phí (0.15%)</span>
            <span>{formatCurrency(Math.round(fee))} VNĐ</span>
          </div>
          {side === "SELL" && (
            <div className="flex justify-between text-gray-400">
              <span>Thuế TNCN (0.1%)</span>
              <span>{formatCurrency(Math.round(tax))} VNĐ</span>
            </div>
          )}
          <div className="flex justify-between font-semibold border-t border-dark-border pt-2">
            <span className="text-gray-300">{side === "BUY" ? "Tiền cần có" : "Tiền nhận về"}</span>
            <span className={side === "BUY" ? "text-price-down" : "text-price-up"}>
              {formatCurrency(Math.round(netTotal))} VNĐ
            </span>
          </div>
        </div>

        {/* Số dư */}
        <div className="text-xs text-gray-500 text-right">
          Khả dụng: {formatCurrency(user?.wallet?.available_balance)} VNĐ
        </div>

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 rounded-lg font-semibold text-white transition disabled:opacity-50 ${
            side === "BUY" ? "bg-price-up hover:bg-green-600" : "bg-price-down hover:bg-red-700"
          }`}
        >
          {loading ? "Đang đặt lệnh..." : `Đặt lệnh ${side === "BUY" ? "MUA" : "BÁN"} ${stock.symbol}`}
        </button>
      </form>
    </div>
  );
}
