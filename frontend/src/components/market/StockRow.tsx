"use client";
import { useRef, useEffect, useState } from "react";
import Link from "next/link";
import { Stock } from "@/types/market";
import { getPriceColor, getPriceColorClass } from "@/utils/calculators";
import { formatVolume, formatPercent } from "@/utils/formatters";

function p(val: number | null | undefined): string {
  if (val == null) return "—";
  return (val / 1000).toFixed(2);
}

interface Props {
  stock: Stock;
}

export default function StockRow({ stock }: Props) {
  const snap = stock.latest_price;
  const prevPriceRef = useRef<number | null>(null);
  const [blinkClass, setBlinkClass] = useState("");

  useEffect(() => {
    if (!snap) return;
    const prev = prevPriceRef.current;
    if (prev !== null && prev !== snap.current_price) {
      const cls = snap.current_price > prev ? "blink-up" : "blink-down";
      setBlinkClass(cls);
      const t = setTimeout(() => setBlinkClass(""), 600);
      return () => clearTimeout(t);
    }
    prevPriceRef.current = snap.current_price;
  }, [snap?.current_price]);

  if (!snap) {
    return (
      <tr className="border-b border-dark-border/50 hover:bg-dark-bg/50">
        <td className="px-2 py-2">
          <Link href={`/market/${stock.symbol}`} className="font-semibold text-white hover:text-price-up">
            {stock.symbol}
          </Link>
        </td>
        {Array(16).fill(null).map((_, i) => (
          <td key={i} className="px-2 py-2 text-right text-gray-600">—</td>
        ))}
      </tr>
    );
  }

  const color = getPriceColor(snap.current_price, snap);
  const colorCls = getPriceColorClass(color);

  return (
    <tr className={`border-b border-dark-border/50 hover:bg-dark-bg/50 transition-colors ${blinkClass}`}>
      <td className="px-2 py-2">
        <Link href={`/market/${stock.symbol}`} className="font-semibold text-white hover:text-price-up">
          {stock.symbol}
        </Link>
      </td>
      <td className="px-2 py-2 text-right text-price-ceiling">{p(snap.ceiling_price)}</td>
      <td className="px-2 py-2 text-right text-price-ref">{p(snap.reference_price)}</td>
      <td className="px-2 py-2 text-right text-price-floor">{p(snap.floor_price)}</td>
      {/* Dư mua top 3 */}
      <td className="px-2 py-2 text-right text-gray-400">{formatVolume(snap.bid_vol_3)}</td>
      <td className="px-2 py-2 text-right text-price-up">{p(snap.bid_price_3)}</td>
      <td className="px-2 py-2 text-right text-gray-400">{formatVolume(snap.bid_vol_2)}</td>
      <td className="px-2 py-2 text-right text-price-up">{p(snap.bid_price_2)}</td>
      <td className="px-2 py-2 text-right text-gray-400">{formatVolume(snap.bid_vol_1)}</td>
      <td className="px-2 py-2 text-right text-price-up">{p(snap.bid_price_1)}</td>
      {/* Giá khớp */}
      <td className={`px-2 py-2 text-right font-bold ${colorCls}`}>{p(snap.current_price)}</td>
      <td className="px-2 py-2 text-right text-gray-400">{formatVolume(snap.volume)}</td>
      {/* Thay đổi */}
      <td className={`px-2 py-2 text-right ${colorCls}`}>
        {snap.change >= 0 ? "+" : ""}{p(snap.change)}
      </td>
      <td className={`px-2 py-2 text-right ${colorCls}`}>
        {formatPercent(snap.change_percent)}
      </td>
      {/* Dư bán */}
      <td className="px-2 py-2 text-right text-price-down">{p(snap.ask_price_1)}</td>
      <td className="px-2 py-2 text-right text-gray-400">{formatVolume(snap.ask_vol_1)}</td>
      {/* KLGD */}
      <td className="px-2 py-2 text-right text-gray-400">{formatVolume(snap.volume)}</td>
    </tr>
  );
}
