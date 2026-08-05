"use client";

import { createContext, useContext, useEffect, useState } from "react";
import * as api from "@/lib/api";
import type { AppUser } from "@/lib/types";

interface AuthContextValue {
  user: AppUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  loginWithToken: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .getMe()
      .then(setUser)
      .catch(() => api.clearToken())
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const res = await api.login(email, password);
    api.setToken(res.access_token);
    setUser(res.user);
  }

  async function signup(email: string, password: string) {
    const res = await api.signup(email, password);
    api.setToken(res.access_token);
    setUser(res.user);
  }

  async function loginWithToken(token: string) {
    api.setToken(token);
    const me = await api.getMe();
    setUser(me);
  }

  function logout() {
    api.clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, loginWithToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
