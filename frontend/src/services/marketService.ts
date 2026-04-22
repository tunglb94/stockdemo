import apiClient from "./apiClient";
import { Stock, CandleData } from "@/types/market";

export const marketService = {
  async getStocks(vn30Only = false): Promise<Stock[]> {
    const res = await apiClient.get<{ results: Stock[] }>("/market/stocks/", {
      params: vn30Only ? { vn30: 1 } : {},
    });
    return res.data.results ?? (res.data as unknown as Stock[]);
  },

  async getStock(symbol: string): Promise<Stock> {
    const res = await apiClient.get<Stock>(`/market/stocks/${symbol}/`);
    return res.data;
  },

  async getHistory(symbol: string, start: string, end: string, interval = "1D"): Promise<CandleData[]> {
    const res = await apiClient.get<CandleData[]>(`/market/stocks/${symbol}/history/`, {
      params: { start, end, interval },
    });
    return res.data;
  },

  async getOverview() {
    const res = await apiClient.get("/market/overview/");
    return res.data;
  },
};
