"use client";
import { Stock } from "@/types/market";
import StockRow from "./StockRow";

const HEADERS = [
  { label: "Mã CK",    cls: "text-left sticky left-0 bg-dark-surface z-10 w-16" },
  { label: "Trần",     cls: "text-right text-price-ceiling w-14" },
  { label: "TC",       cls: "text-right text-price-ref w-14" },
  { label: "Sàn",      cls: "text-right text-price-floor w-14" },
  { label: "Dư M3",    cls: "text-right text-gray-500 w-14" },
  { label: "Mua 3",    cls: "text-right w-14" },
  { label: "Dư M2",    cls: "text-right text-gray-500 w-14" },
  { label: "Mua 2",    cls: "text-right w-14" },
  { label: "Dư M1",    cls: "text-right text-gray-500 w-14" },
  { label: "Mua 1",    cls: "text-right w-14" },
  { label: "Khớp",     cls: "text-right font-semibold w-16" },
  { label: "KL",       cls: "text-right text-gray-500 w-16" },
  { label: "+/-",      cls: "text-right w-14" },
  { label: "%",        cls: "text-right w-14" },
  { label: "Bán 1",    cls: "text-right w-14" },
  { label: "Dư B1",    cls: "text-right text-gray-500 w-14" },
  { label: "Cao",      cls: "text-right text-gray-500 w-14" },
  { label: "Thấp",     cls: "text-right text-gray-500 w-14" },
  { label: "KLGD",     cls: "text-right text-gray-500 w-16" },
];

export default function StockBoard({ stocks }: { stocks: Stock[] }) {
  return (
    <div className="h-full overflow-auto">
      <table className="w-full text-xs border-collapse">
        <thead className="sticky top-0 z-20">
          <tr className="bg-[#1a1b20] border-b border-dark-border">
            {HEADERS.map((h) => (
              <th key={h.label}
                className={`px-1.5 py-1.5 font-medium whitespace-nowrap ${h.cls}`}>
                {h.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {stocks.length === 0 ? (
            <tr>
              <td colSpan={HEADERS.length} className="text-center py-12 text-gray-600">
                Không có dữ liệu
              </td>
            </tr>
          ) : (
            stocks.map((stock) => <StockRow key={stock.symbol} stock={stock} />)
          )}
        </tbody>
      </table>
    </div>
  );
}
