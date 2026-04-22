"use client";
import { Stock } from "@/types/market";
import StockRow from "./StockRow";

interface Props {
  stocks: Stock[];
}

const HEADERS = [
  { label: "Mã CK", cls: "text-left w-20" },
  { label: "Trần", cls: "text-right text-price-ceiling w-20" },
  { label: "TC", cls: "text-right text-price-ref w-20" },
  { label: "Sàn", cls: "text-right text-price-floor w-20" },
  { label: "Dư mua 3", cls: "text-right text-gray-400 w-16" },
  { label: "Giá mua 3", cls: "text-right text-gray-400 w-20" },
  { label: "Dư mua 2", cls: "text-right text-gray-400 w-16" },
  { label: "Giá mua 2", cls: "text-right text-gray-400 w-20" },
  { label: "Dư mua 1", cls: "text-right text-gray-400 w-16" },
  { label: "Giá mua 1", cls: "text-right text-gray-400 w-20" },
  { label: "Giá khớp", cls: "text-right font-bold w-24" },
  { label: "KL khớp", cls: "text-right text-gray-400 w-20" },
  { label: "+/-", cls: "text-right w-20" },
  { label: "%", cls: "text-right w-16" },
  { label: "Giá bán 1", cls: "text-right text-gray-400 w-20" },
  { label: "Dư bán 1", cls: "text-right text-gray-400 w-16" },
  { label: "KLGD", cls: "text-right text-gray-400 w-20" },
];

export default function StockBoard({ stocks }: Props) {
  if (!stocks.length) {
    return (
      <div className="bg-dark-surface border border-dark-border rounded-xl p-8 text-center text-gray-500">
        Đang tải dữ liệu...
      </div>
    );
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-border">
              {HEADERS.map((h) => (
                <th key={h.label} className={`px-2 py-2.5 text-xs ${h.cls}`}>
                  {h.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => (
              <StockRow key={stock.symbol} stock={stock} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
