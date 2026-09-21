"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, ApiUser } from "./api";

const TOKEN_KEY = "nextmove_token";

interface AuthContextValue {
  token: string | null;
  user: ApiUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, preferredSport: string) => Promise<void>;
  logout: () => void;
  updateSport: (sport: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<ApiUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Au premier chargement : on relit le token stocké et on vérifie qu'il est
  // toujours valide auprès du serveur (comme fetchMe() côté iOS).
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setIsLoading(false);
      return;
    }
    api
      .me(stored)
      .then((u) => {
        setToken(stored);
        setUser(u);
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
      })
      .finally(() => setIsLoading(false));
  }, []);

  function applySession(accessToken: string, apiUser: ApiUser) {
    setToken(accessToken);
    setUser(apiUser);
    localStorage.setItem(TOKEN_KEY, accessToken);
  }

  async function login(email: string, password: string) {
    const auth = await api.login(email, password);
    applySession(auth.access_token, auth.user);
  }

  async function register(email: string, password: string, preferredSport: string) {
    const auth = await api.register(email, password, preferredSport);
    applySession(auth.access_token, auth.user);
  }

  function logout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
  }

  async function updateSport(sport: string) {
    if (!token) return;
    const updated = await api.updateSport(token, sport);
    setUser(updated);
  }

  return (
    <AuthContext.Provider value={{ token, user, isLoading, login, register, logout, updateSport }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé à l'intérieur de <AuthProvider>");
  return ctx;
}