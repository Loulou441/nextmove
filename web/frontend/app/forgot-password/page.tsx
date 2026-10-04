"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export default function ForgotPasswordPage() {
  const router = useRouter();

  const [step, setStep] = useState<"request" | "reset">("request");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleRequestCode(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.forgotPassword(email);
      setStep("reset");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResetPassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.resetPassword(email, code, newPassword);
      router.push("/login");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Code invalide ou expiré.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center p-6">
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 w-full max-w-sm">
        {step === "request" ? (
          <>
            <div className="text-center mb-6">
              <h1 className="text-xl font-bold text-nm-text mb-2">Mot de passe oublié</h1>
              <p className="text-sm text-nm-text-secondary">
                Entre ton email, on t'enverra un code de réinitialisation.
              </p>
            </div>

            <form onSubmit={handleRequestCode} className="flex flex-col gap-4">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-nm-button border border-nm-border px-4 py-2.5 text-sm text-nm-text focus:outline-none focus:ring-2 focus:ring-nm-green"
                placeholder="toi@exemple.com"
              />

              {error && (
                <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-2.5 text-sm text-nm-orange">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button py-3 text-sm transition-colors disabled:opacity-60"
              >
                {isSubmitting ? "Envoi..." : "Envoyer le code"}
              </button>
            </form>
          </>
        ) : (
          <>
            <div className="text-center mb-6">
              <h1 className="text-xl font-bold text-nm-text mb-2">Nouveau mot de passe</h1>
              <p className="text-sm text-nm-text-secondary">
                Entre le code reçu par email et ton nouveau mot de passe.
              </p>
            </div>

            <form onSubmit={handleResetPassword} className="flex flex-col gap-4">
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

              <input
                type="password"
                required
                minLength={6}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-nm-button border border-nm-border px-4 py-2.5 text-sm text-nm-text focus:outline-none focus:ring-2 focus:ring-nm-green"
                placeholder="Nouveau mot de passe (6 caractères min.)"
              />

              {error && (
                <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-2.5 text-sm text-nm-orange">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting || code.length !== 6}
                className="bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button py-3 text-sm transition-colors disabled:opacity-60"
              >
                {isSubmitting ? "Réinitialisation..." : "Réinitialiser"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}