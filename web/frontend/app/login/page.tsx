"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";

const SPORTS = [
  { value: "padel", label: "🥎 Padel" },
  { value: "pickleball", label: "🏓 Pickleball" },
  { value: "tennis", label: "🎾 Tennis" },
];

export default function LoginPage() {
  const router = useRouter();
  const { login, register } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [sport, setSport] = useState("padel");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, sport);
      }
      router.push("/library");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center p-6">
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">🏓</div>
          <h1 className="text-2xl font-bold text-nm-text">NextMove</h1>
        </div>

        {/* Sélecteur Login / Register */}
        <div className="flex bg-nm-bg rounded-nm-button p-1 mb-6">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`flex-1 py-2 rounded-[10px] text-sm font-semibold transition-colors ${
              mode === "login" ? "bg-nm-card text-nm-text shadow-sm" : "text-nm-text-secondary"
            }`}
          >
            Connexion
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`flex-1 py-2 rounded-[10px] text-sm font-semibold transition-colors ${
              mode === "register" ? "bg-nm-card text-nm-text shadow-sm" : "text-nm-text-secondary"
            }`}
          >
            Inscription
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-nm-text mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-nm-button border border-nm-border px-4 py-2.5 text-sm text-nm-text focus:outline-none focus:ring-2 focus:ring-nm-green"
              placeholder="toi@exemple.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-nm-text mb-1">Mot de passe</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-nm-button border border-nm-border px-4 py-2.5 text-sm text-nm-text focus:outline-none focus:ring-2 focus:ring-nm-green"
              placeholder="Au moins 6 caractères"
            />
          </div>

          {mode === "register" && (
            <div>
              <label className="block text-sm font-medium text-nm-text mb-2">Sport principal</label>
              <div className="flex gap-2">
                {SPORTS.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => setSport(s.value)}
                    className={`flex-1 py-2 rounded-nm-button text-sm font-medium border transition-colors ${
                      sport === s.value
                        ? "bg-nm-green-light border-nm-green text-nm-text"
                        : "border-nm-border text-nm-text-secondary"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-2.5 text-sm text-nm-orange">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button py-3 text-sm transition-colors disabled:opacity-60"
          >
            {isSubmitting
              ? "Un instant..."
              : mode === "login"
              ? "Se connecter"
              : "Créer mon compte"}
          </button>
        </form>
      </div>
    </div>
  );
}