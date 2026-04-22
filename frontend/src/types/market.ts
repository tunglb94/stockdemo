export interface PriceSnapshot {
  reference_price: number;
  ceiling_price: number;
  floor_price: number;
  current_price: number;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  volume: number;
  value: number;
  change: number;
  change_percent: number;
  bid_price_1: number | null;
  bid_vol_1: number | null;
  bid_price_2: number | null;
  bid_vol_2: number | null;
  bid_price_3: number | null;
  bid_vol_3: number | null;
  ask_price_1: number | null;
  ask_vol_1: number | null;
  ask_price_2: number | null;
  ask_vol_2: number | null;
  ask_price_3: number | null;
  ask_vol_3: number | null;
  timestamp: string;
}

export interface Stock {
  id: number;
  symbol: string;
  company_name: string;
  exchange: "HOSE" | "HNX" | "UPCOM";
  industry: string;
  is_vn30: boolean;
  latest_price: PriceSnapshot | null;
}

export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type PriceColor = "up" | "down" | "ceiling" | "floor" | "ref";
