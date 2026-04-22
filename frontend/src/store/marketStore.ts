import { create } from "zustand";
import { Stock } from "@/types/market";

interface MarketState {
  stocks: Stock[];
  lastUpdated: Date | null;
  setStocks: (stocks: Stock[]) => void;
  updateStockPrice: (symbol: string, snapshot: Stock["latest_price"]) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  stocks: [],
  lastUpdated: null,

  setStocks: (stocks) => set({ stocks, lastUpdated: new Date() }),

  updateStockPrice: (symbol, snapshot) =>
    set((state) => ({
      stocks: state.stocks.map((s) =>
        s.symbol === symbol ? { ...s, latest_price: snapshot } : s
      ),
      lastUpdated: new Date(),
    })),
}));
