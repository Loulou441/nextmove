"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";

const SPORTS = [
  { value: "padel", label: "🥎 Padel" },
  { value: "pickleball", label: "🏓 Pickleball" },
  { value: "tennis", label: "🎾 Tennis" },
];

export default function UploadPage() {
  const router = useRouter();
  const { token } = useAuth();

  const [title, setTitle] = useState("");
  const [sport, setSport] = useState("padel");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [step, setStep] = useState<"idle" | "uploading" | "starting">("idle");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !file) return;

    setError(null);
    setIsSubmitting(true);

    try {
      setStep("uploading");
      const match = await api.createMatch(token, title, sport, file);

      setStep("starting");
      await api.analyzeMatch(token, match.id);

      router.push(`/library/${match.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
      setIsSubmitting(false);
      setStep("idle");
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-3xl font-bold text-nm-text mb-8">Nouveau match</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <div>
          <label className="block text-base font-medium text-nm-text mb-2">Titre du match</label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-nm-button border border-nm-border px-5 py-3.5 text-base text-nm-text focus:outline-none focus:ring-2 focus:ring-nm-green bg-nm-card"
            placeholder="Ex. Match du samedi"
          />
        </div>

        <div>
          <label className="block text-base font-medium text-nm-text mb-3">Sport</label>
          <div className="flex gap-3">
            {SPORTS.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => setSport(s.value)}
                className={`flex-1 py-3.5 rounded-nm-button text-base font-medium border transition-colors ${
                  sport === s.value
                    ? "bg-nm-green-light border-nm-green text-nm-text"
                    : "border-nm-border text-nm-text-secondary bg-nm-card"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-base font-medium text-nm-text mb-2">Vidéo du match</label>
          <input
            type="file"
            required
            accept="video/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="w-full text-base text-nm-text-secondary file:mr-4 file:py-3 file:px-5 file:rounded-nm-button file:border-0 file:bg-nm-green-light file:text-nm-green file:font-semibold file:text-base"
          />
          <p className="text-sm text-nm-text-secondary mt-2">Taille maximale : 50 Mo.</p>
        </div>

        {error && (
          <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-5 py-3 text-base text-nm-orange">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting || !file}
          className="mt-2 bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button py-4 text-base transition-colors disabled:opacity-60"
        >
          {step === "uploading" && "Envoi de la vidéo..."}
          {step === "starting" && "Démarrage de l'analyse..."}
          {step === "idle" && "Analyser ce match"}
        </button>
      </form>
    </div>
  );
}