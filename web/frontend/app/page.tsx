"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="flex flex-col flex-1 items-center justify-center">
        <p className="text-nm-text-secondary text-sm">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center gap-4 p-8">
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center max-w-sm">
        <div className="text-4xl mb-3">🏓</div>
        <h1 className="text-2xl font-bold text-nm-text mb-2">NextMove</h1>

        {user ? (
          <>
            <p className="text-nm-text-secondary text-sm mb-4">
              Connecté en tant que <span className="text-nm-text font-medium">{user.email}</span>
            </p>
            <button
              onClick={logout}
              className="text-nm-red text-sm font-semibold"
            >
              Se déconnecter
            </button>
          </>
        ) : (
          <>
            <p className="text-nm-text-secondary text-sm mb-4">
              Ton coach personnel de sports de raquette, propulsé par l'IA.
            </p>
            <Link
              href="/login"
              className="inline-block bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button px-6 py-2.5 text-sm transition-colors"
            >
              Se connecter
            </Link>
          </>
        )}
      </div>
    </div>
  );
}