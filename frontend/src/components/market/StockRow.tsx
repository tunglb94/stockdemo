"use client";
import { useRef, useEffect, useState } from "react";
import Link from "next/link";
import { Stock } from "@/types/market";
import { getPriceColor, getPriceColorClass } from "@/utils/calculators";
import { formatVolume } from "@/utils/formatters";

function p(val: number | string | null | undefined): string {
  if (val == null) return "—";
  const n = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(n)) return "—";
  return (n / 1000).toFixed(2);
}

function vol(val: number | null | undefined): string {
  if (!val) return "—";
  return formatVolume(val);
}

export default function StockRow({ stock }: { stock: Stock }) {
  const snap = stock.latest_price;
  const prevRef = useRef<number | null>(null);
  const [flash, setFlash] = useState("");

  useEffect(() => {
    if (!snap) return;
    const cur = Number(snap.current_price);
    const prev = prevRef.current;
    if (prev !== null && prev !== cur) {
      setFlash(cur > prev ? "blink-up" : "blink-down");
      const t = setTimeout(() => setFlash(""), 500);
      return () => clearTimeout(t);
    }
    prevRef.current = cur;
  }, [snap?.current_price]);

  const symCell = (
    <td className="px-1.5 py-[3px] sticky left-0 bg-dark-surface z-10 border-r border-dark-border/20">
      <Link href={`/market/${stock.symbol}`}
        className="font-bold text-white hover:text-price-up transition whitespace-nowrap text-xs">
        {stock.symbol}
      </Link>
    </td>
  );

  if (!snap) {
    return (
      <tr className="border-b border-dark-border/20 hover:bg-white/[0.015]">
        {symCell}
        {Array(18).fill(null).map((_, i) => (
          <td key={i} className="px-1.5 py-[3px] text-right text-gray-700 text-xs">—</td>
        ))}
      </tr>
    );
  }

  const cur = Number(snap.current_price);
  const ref = Number(snap.reference_price);
  const ceil = Number(snap.ceiling_price);
  const floor = Number(snap.floor_price);
  const color = getPriceColor(cur, { ...snap, current_price: cur, reference_price: ref, ceiling_price: ceil, floor_price: floor });
  const cls = getPriceColorClass(color);
  const chgNum = Number(snap.change);
  const chgPct = Number(snap.change_percent);

  return (
    <tr className={`border-b border-dark-border/20 hover:bg-white/[0.015] transition-colors text-xs ${flash}`}>
      {symCell}
      <td className="px-1.5 py-[3px] text-right text-price-ceiling tabular-nums">{p(ceil)}</td>
      <td className="px-1.5 py-[3px] text-right text-price-ref tabular-nums">{p(ref)}</td>
      <td className="px-1.5 py-[3px] text-right text-price-floor tabular-nums">{p(floor)}</td>

      <td className="px-1.5 py-[3px] text-right text-gray-600 tabular-nums">{vol(snap.bid_vol_3)}</td>
      <td className="px-1.5 py-[3px] text-right text-price-up tabular-nums">{p(snap.bid_price_3)}</td>
      <td className="px-1.5 py-[3px] text-right text-gray-600 tabular-nums">{vol(snap.bid_vol_2)}</td>
      <td className="px-1.5 py-[3px] text-right text-price-up tabular-nums">{p(snap.bid_price_2)}</td>
      <td className="px-1.5 py-[3px] text-right text-gray-600 tabular-nums">{vol(snap.bid_vol_1)}</td>
      <td className="px-1.5 py-[3px] text-right text-price-up tabular-nums">{p(snap.bid_price_1)}</td>

      <td className={`px-1.5 py-[3px] text-right font-bold tabular-nums ${cls}`}>{p(cur)}</td>
      <td className="px-1.5 py-[3px] text-right text-gray-400 tabular-nums">{vol(snap.volume)}</td>

      <td className={`px-1.5 py-[3px] text-right tabular-nums ${cls}`}>
        {chgNum >= 0 ? "+" : ""}{p(snap.change)}
      </td>
      <td className={`px-1.5 py-[3px] text-right tabular-nums ${cls}`}>
        {chgPct >= 0 ? "+" : ""}{chgPct.toFixed(2)}%
      </td>

      <td className="px-1.5 py-[3px] text-right text-price-down tabular-nums">{p(snap.ask_price_1)}</td>
      <td className="px-1.5 py-[3px] text-right text-gray-600 tabular-nums">{vol(snap.ask_vol_1)}</td>

      <td className="px-1.5 py-[3px] text-right text-gray-400 tabular-nums">{p(snap.high_price)}</td>
      <td className="px-1.5 py-[3px] text-right text-gray-400 tabular-nums">{p(snap.low_price)}</td>
      <td className="px-1.5 py-[3px] text-right text-gray-500 tabular-nums">{vol(snap.volume)}</td>
    </tr>
  );
}
