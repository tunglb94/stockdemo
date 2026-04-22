export interface Wallet {
  balance: number;
  frozen_balance: number;
  available_balance: number;
  updated_at: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  phone: string;
  wallet: Wallet;
  created_at: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
  message?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  phone?: string;
}
