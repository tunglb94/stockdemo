import apiClient from "./apiClient";
import { Order, PlaceOrderPayload, PortfolioSummary, Holding } from "@/types/trading";

export const tradingService = {
  async placeOrder(payload: PlaceOrderPayload): Promise<{ message: string; order: Order }> {
    const res = await apiClient.post("/trading/orders/place/", payload);
    return res.data;
  },

  async cancelOrder(orderId: string): Promise<{ message: string }> {
    const res = await apiClient.post(`/trading/orders/${orderId}/cancel/`);
    return res.data;
  },

  async getOrders(params?: { status?: string; side?: string }): Promise<Order[]> {
    const res = await apiClient.get("/trading/orders/", { params });
    return res.data.results ?? res.data;
  },

  async getPortfolio(): Promise<PortfolioSummary> {
    const res = await apiClient.get<PortfolioSummary>("/trading/portfolio/");
    return res.data;
  },

  async getHoldings(): Promise<Holding[]> {
    const res = await apiClient.get<Holding[]>("/trading/holdings/");
    return res.data;
  },

  async getTPlus() {
    const res = await apiClient.get("/trading/t-plus/");
    return res.data;
  },

  async getStats() {
    const res = await apiClient.get("/trading/stats/");
    return res.data;
  },
};
