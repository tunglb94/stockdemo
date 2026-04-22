import { PriceSnapshot, PriceColor } from "@/types/market";

export function getPriceColor(price: number, snapshot: PriceSnapshot): PriceColor {
  if (price >= snapshot.ceiling_price) return "ceiling";
  if (price <= snapshot.floor_price) return "floor";
  if (price > snapshot.reference_price) return "up";
  if (price < snapshot.reference_price) return "down";
  return "ref";
}

export function getPriceColorClass(color: PriceColor): string {
  const map: Record<PriceColor, string> = {
    up: "text-price-up",
    down: "text-price-down",
    ceiling: "text-price-ceiling",
    floor: "text-price-floor",
    ref: "text-price-ref",
  };
  return map[color];
}

export function calcPnL(avgCost: number, currentPrice: number, quantity: number) {
  const cost = avgCost * quantity;
  const value = currentPrice * quantity;
  const pnl = value - cost;
  const pnlPercent = cost > 0 ? (pnl / cost) * 100 : 0;
  return { pnl, pnlPercent };
}

export function calcTradingFee(price: number, quantity: number, feeRate = 0.0015): number {
  return price * quantity * feeRate;
}

export function calcSellTax(price: number, quantity: number, taxRate = 0.001): number {
  return price * quantity * taxRate;
}

export function roundToLot(quantity: number): number {
  return Math.floor(quantity / 100) * 100;
}
