"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, ApiUser } from "./api";

interface AuthContextValue {
  user: ApiUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, preferredSport: string) => Promise<void>;
  logout: () => void;
  updateSport: (sport: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ApiUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Au premier chargement : le cookie httpOnly (s'il existe) est envoyé
  // automatiquement par le navigateur — on vérifie juste s'il y a une
  // session valide en interrogeant le serveur (comme fetchMe() côté iOS).
  // Plus de lecture/écriture de localStorage : le token est invisible pour
  // le JavaScript, c'est tout l'intérêt du cookie httpOnly.
  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const auth = await api.login(email, password);
    setUser(auth.user);
  }

  async function register(email: string, password: string, preferredSport: string) {
    const auth = await api.register(email, password, preferredSport);
    setUser(auth.user);
  }

  async function logout() {
    await api.logout().catch(() => {});
    setUser(null);
  }

  async function updateSport(sport: string) {
    const updated = await api.updateSport(sport);
    setUser(updated);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, updateSport }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé à l'intérieur de <AuthProvider>");
  return ctx;
}