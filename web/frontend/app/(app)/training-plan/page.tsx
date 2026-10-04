"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, TrainingPlan, ApiError } from "@/lib/api";

const SPORTS = [
  { value: "padel", label: "🥎 Padel" },
  { value: "pickleball", label: "🏓 Pickleball" },
  { value: "tennis", label: "🎾 Tennis" },
];

export default function TrainingPlanPage() {
  const { user } = useAuth();
  const [sport, setSport] = useState(user?.preferred_sport ?? "padel");
  const [plans, setPlans] = useState<TrainingPlan[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoadingHistory(true);
    setError(null);
    api
      .getTrainingPlans(sport)
      .then((saved) => { if (!cancelled) setPlans(saved); })
      .catch(() => { if (!cancelled) setPlans([]); })
      .finally(() => { if (!cancelled) setIsLoadingHistory(false); });
    return () => { cancelled = true; };
  }, [sport]);

  async function handleGenerate() {
    setError(null);
    setIsGenerating(true);
    try {
      const plan = await api.generateTrainingPlan(sport);
      setPlans((prev) => [plan, ...prev]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Le programme n'a pas pu être généré."
      );
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleDelete(planId: string) {
    setIsDeleting(true);
    try {
      await api.deleteTrainingPlan(planId);
      setPlans((prev) => prev.filter((p) => p.id !== planId));
    } catch {
      setError("Impossible de supprimer ce programme.");
    } finally {
      setIsDeleting(false);
    }
  }

  const latestPlan = plans[0];

  return (
    <div className="max-w-2xl flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold text-nm-text mb-1">Programme d’entraînement</h1>
        <p className="text-nm-text-secondary text-sm">
          Généré à partir de tes matchs analysés récemment.
        </p>
      </div>

      <div className="flex gap-2">
        {SPORTS.map((s) => (
          <button
            key={s.value}
            disabled={isGenerating}
            onClick={() => {
              if (sport === s.value) return;
              setIsLoadingHistory(true);
              setPlans([]);
              setSport(s.value);
            }}
            className={`flex-1 py-2 rounded-nm-button text-sm font-medium border transition-colors ${
              sport === s.value
                ? "bg-nm-green-light border-nm-green text-nm-text"
                : "border-nm-border text-nm-text-secondary bg-nm-card"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <button
        onClick={handleGenerate}
        disabled={isGenerating || isLoadingHistory}
        className="bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button py-3 text-sm transition-colors disabled:opacity-60"
      >
        {isGenerating ? "Génération en cours..." : "Générer un nouveau programme"}
      </button>

      {error && (
        <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-2.5 text-sm text-nm-orange">
          {error}
        </div>
      )}

      {isLoadingHistory && (
        <p className="text-nm-text-secondary text-sm">Chargement de l’historique...</p>
      )}

      {!isLoadingHistory && !latestPlan && !error && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
          <p className="text-nm-text-secondary text-sm">
            Aucun programme pour ce sport pour l’instant. Génère-en un à partir de tes matchs analysés.
          </p>
        </div>
      )}

      {latestPlan && !error && (
        <div className="flex flex-col gap-3">
          <div className="flex justify-end">
            <button
              onClick={() => handleDelete(latestPlan.id)}
              disabled={isDeleting}
              className="text-nm-red text-xs font-medium hover:underline disabled:opacity-60"
            >
              {isDeleting ? "Suppression..." : "🗑️ Supprimer ce programme"}
            </button>
          </div>

          {latestPlan.content.recommandations_coach.map((rec, i) => (
            <div key={i} className="bg-nm-card rounded-nm-card shadow-sm p-4">
              <p className="font-semibold text-nm-text text-sm mb-3">{rec.titre}</p>

              <div className="flex flex-col gap-2 text-sm">
                <div>
                  <span className="text-nm-text-secondary font-medium">Constat — </span>
                  <span className="text-nm-text">{rec.contenu.constat}</span>
                </div>
                <div>
                  <span className="text-nm-text-secondary font-medium">Analyse — </span>
                  <span className="text-nm-text">{rec.contenu.analyse}</span>
                </div>
                <div className="bg-nm-card-green border border-nm-card-green-border rounded-nm-button px-3 py-2.5">
                  <span className="font-medium text-nm-green">Exercice recommandé — </span>
                  <span className="text-nm-text">{rec.contenu.action_corrective}</span>
                </div>
                <div className="text-nm-text-secondary italic">💡 {rec.contenu.pro_tip}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}