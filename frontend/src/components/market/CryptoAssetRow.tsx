"use client";
import { useRef, useEffect, useState, memo } from "react";

export interface AssetPrice {
  symbol: string;
  price: number;
  change_24h: number;
  updated_at: string | null;
}

export interface Asset extends AssetPrice {
  name: string;
  category: string;
  rank: number;
  volume_24h: number;
  market_cap: number;
}

function fmtPrice(p: number): string {
  if (p === 0) return "—";
  if (p >= 10000) return p.toLocaleString("en-US", { maximumFractionDigits: 0 });
  if (p >= 1000)  return p.toLocaleString("en-US", { maximumFractionDigits: 1 });
  if (p >= 1)     return p.toFixed(3);
  if (p >= 0.01)  return p.toFixed(5);
  return p.toFixed(8);
}

function fmtMcap(v: number): string {
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9)  return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6)  return `$${(v / 1e6).toFixed(1)}M`;
  return `$${v.toFixed(0)}`;
}

function TickCell({
  value,
  className = "",
  children,
}: {
  value: number;
  className?: string;
  children: React.ReactNode;
}) {
  const prevRef = useRef<number>(value);
  const [flash, setFlash] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const prev = prevRef.current;
    if (prev !== value) {
      if (timerRef.current) clearTimeout(timerRef.current);
      const dir = value > prev ? "tick-up" : "tick-down";
      setFlash(dir);
      timerRef.current = setTimeout(() => setFlash(""), 950);
      prevRef.current = value;
    }
  }, [value]);

  return (
    <td className={`px-2 md:px-3 py-2 text-right tabular-nums ${className} ${flash}`}>
      {children}
    </td>
  );
}

const CryptoAssetRow = memo(function CryptoAssetRow({ asset }: { asset: Asset }) {
  const up   = asset.change_24h > 0;
  const down = asset.change_24h < 0;
  const chgColor = up ? "text-price-up" : down ? "text-price-down" : "text-gray-400";

  return (
    <tr className="border-t border-dark-border/30 hover:bg-white/[0.02] transition-colors">
      {/* Rank */}
      <td className="px-2 md:px-3 py-2 text-gray-600 text-xs w-8 text-right">{asset.rank}</td>

      {/* Symbol + Name */}
      <td className="px-2 md:px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className={`hidden sm:inline text-[9px] px-1 py-0.5 rounded font-bold leading-none ${
            asset.category === "COMMODITY"
              ? "bg-yellow-900/50 text-yellow-400"
              : "bg-blue-900/50 text-blue-300"
          }`}>
            {asset.category === "COMMODITY" ? "CMD" : "C"}
          </span>
          <span className="font-bold text-white text-xs md:text-sm">{asset.symbol}</span>
          <span className="hidden md:inline text-gray-500 text-xs truncate max-w-[100px]">{asset.name}</span>
        </div>
      </td>

      {/* Price — flashes on change */}
      <TickCell value={asset.price} className={`font-bold text-xs md:text-sm ${chgColor}`}>
        ${fmtPrice(asset.price)}
      </TickCell>

      {/* 24h % — flashes on change */}
      <TickCell value={asset.change_24h} className={`font-semibold text-xs ${chgColor}`}>
        {asset.change_24h === 0
          ? "—"
          : `${up ? "▲" : "▼"} ${Math.abs(asset.change_24h).toFixed(2)}%`}
      </TickCell>

      {/* Volume — hidden on mobile */}
      <td className="hidden md:table-cell px-3 py-2 text-right text-gray-500 text-xs">
        {asset.volume_24h > 0 ? fmtMcap(asset.volume_24h) : "—"}
      </td>

      {/* Market cap — hidden on mobile */}
      <td className="hidden md:table-cell px-3 py-2 text-right text-gray-500 text-xs">
        {asset.market_cap > 0 ? fmtMcap(asset.market_cap) : "—"}
      </td>

      {/* Updated — hidden on small */}
      <td className="hidden lg:table-cell px-3 py-2 text-right text-gray-700 text-xs">
        {asset.updated_at || "—"}
      </td>
    </tr>
  );
});

export default CryptoAssetRow;
