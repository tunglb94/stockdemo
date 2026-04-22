"use client";
import { useEffect, useState } from "react";
import { tradingService } from "@/services/tradingService";
import { PortfolioSummary } from "@/types/trading";
import HoldingTable from "@/components/portfolio/HoldingTable";
import PnLSummary from "@/components/portfolio/PnLSummary";
import { formatCurrency, formatPercent } from "@/utils/formatters";

export default function PortfolioPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    tradingService.getPortfolio()
      .then(setSummary)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400 p-4">Đang tải...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">Danh mục đầu tư</h1>
      {summary && (
        <>
          <PnLSummary summary={summary} />
          <HoldingTable holdings={summary.holdings} />
        </>
      )}
    </div>
  );
}
