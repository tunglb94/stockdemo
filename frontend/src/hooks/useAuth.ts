"use client";
import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";

export function useAuth() {
  const { user, isAuthenticated, setAuth, logout, updateUser } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token && !isAuthenticated) {
      authService.getProfile()
        .then((profile) => {
          const refresh = localStorage.getItem("refresh_token") || "";
          setAuth(profile, token, refresh);
        })
        .catch(() => logout());
    }
  }, []);

  return { user, isAuthenticated, logout, updateUser };
}
