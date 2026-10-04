"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function VerifyEmailPage() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResending, setIsResending] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.verifyEmail(code);
      await refreshUser();
      router.push("/library");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Code invalide.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResend() {
    setError(null);
    setMessage(null);
    setIsResending(true);
    try {
      await api.resendVerification();
      setMessage("Un nouveau code vient d'être envoyé.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de renvoyer le code.");
    } finally {
      setIsResending(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center p-6">
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="text-xl font-bold text-nm-text mb-2">Confirme ton email</h1>
          <p className="text-sm text-nm-text-secondary">
            On a envoyé un code à 6 chiffres à {user?.email ?? "ton adresse"}.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            required
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            className="w-full text-center text-2xl tracking-[0.5em] rounded-nm-button border border-nm-border px-4 py-3 text-nm-text focus:outline-none focus:ring-2 focus:ring-nm-green"
            placeholder="______"
          />

          {error && (
            <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-2.5 text-sm text-nm-orange">
              {error}
            </div>
          )}
          {message && (
            <div className="bg-nm-green-light border border-nm-green rounded-nm-button px-4 py-2.5 text-sm text-nm-green">
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || code.length !== 6}
            className="bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button py-3 text-sm transition-colors disabled:opacity-60"
          >
            {isSubmitting ? "Vérification..." : "Confirmer"}
          </button>

          <button
            type="button"
            onClick={handleResend}
            disabled={isResending}
            className="text-sm text-nm-text-secondary hover:underline disabled:opacity-60"
          >
            {isResending ? "Envoi..." : "Renvoyer le code"}
          </button>
        </form>
      </div>
    </div>
  );
}