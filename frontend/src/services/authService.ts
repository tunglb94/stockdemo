import apiClient from "./apiClient";
import { AuthResponse, LoginPayload, RegisterPayload, User } from "@/types/auth";

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>("/accounts/login/", payload);
    return res.data;
  },

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>("/accounts/register/", payload);
    return res.data;
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/accounts/logout/", { refresh: refreshToken });
  },

  async getProfile(): Promise<User> {
    const res = await apiClient.get<User>("/accounts/profile/");
    return res.data;
  },
};
