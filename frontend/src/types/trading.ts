export type OrderSide = "BUY" | "SELL";
export type OrderType = "LO" | "MP" | "ATO" | "ATC";
export type OrderStatus = "PENDING" | "MATCHED" | "PARTIAL" | "CANCELLED" | "REJECTED";

export interface Transaction {
  quantity: number;
  price: number;
  amount: number;
  fee: number;
  tax: number;
  created_at: string;
}

export interface Order {
  id: string;
  stock_symbol: string;
  stock_name: string;
  order_type: OrderType;
  side: OrderSide;
  quantity: number;
  price: number | null;
  matched_quantity: number;
  matched_price: number | null;
  remaining_quantity: number;
  status: OrderStatus;
  reject_reason: string;
  frozen_amount: number;
  transactions: Transaction[];
  created_at: string;
  updated_at: string;
}

export interface PlaceOrderPayload {
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: number;
  price?: number | null;
}

export interface Holding {
  symbol: string;
  company_name: string;
  quantity: number;
  available_quantity: number;
  frozen_quantity: number;
  avg_cost: number;
  market_value: number;
  unrealized_pnl: number;
}

export interface PortfolioSummary {
  wallet: {
    balance: number;
    frozen_balance: number;
    available_balance: number;
  };
  holdings: Holding[];
  total_cost: number;
  total_market_value: number;
  total_assets: number;
  total_pnl: number;
  total_pnl_percent: number;
}
