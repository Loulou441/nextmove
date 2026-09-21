"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Match, ApiError } from "@/lib/api";
import Link from "next/link";

const SPORT_LABEL: Record<string, string> = {
  padel: "🥎 Padel",
  pickleball: "🏓 Pickleball",
  tennis: "🎾 Tennis",
};

export default function MePage() {
  const { user, token, logout, updateSport } = useAuth();
  const [matches, setMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingSport, setIsUpdatingSport] = useState(false);

  useEffect(() => {
    if (!token) return;
    api
      .getMatches(token)
      .then(setMatches)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [token]);

  async function handleSportChange(sport: string) {
    if (sport === user?.preferred_sport) return;
    setIsUpdatingSport(true);
    try {
      await updateSport(sport);
    } catch {
      // Erreur silencieuse ici, acceptable pour un simple changement de préférence.
    } finally {
      setIsUpdatingSport(false);
    }
  }

  const readyMatches = matches.filter((m) => m.status === "ready" && m.rating != null);
  const averageRating =
    readyMatches.length > 0
      ? (readyMatches.reduce((sum, m) => sum + (m.rating ?? 0), 0) / readyMatches.length).toFixed(1)
      : "0.0";
  const gamesAnalyzed = readyMatches.length;

  if (!user) return null;

  return (
    <div className="flex flex-col gap-5 max-w-xl">
      {/* Player Profile */}
      <div className="bg-nm-card rounded-nm-card shadow-sm p-10 text-center">
        <div className="w-24 h-24 rounded-full bg-nm-green mx-auto mb-4 flex items-center justify-center">
          <span className="text-4xl text-white">🎾</span>
        </div>
        <p className="font-bold text-nm-text text-lg">{user.email}</p>
        <p className="text-nm-text-secondary text-base mt-1">
          {SPORT_LABEL[user.preferred_sport] ?? user.preferred_sport}
        </p>
      </div>

      {/* Progress */}
      <div>
        <p className="text-base font-semibold text-nm-text mb-3">Progress</p>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-nm-card rounded-nm-card shadow-sm p-6">
            <div className="text-nm-green text-3xl mb-2">⭐</div>
            <div className="text-3xl font-bold text-nm-text">
              {isLoading ? "-" : averageRating}
            </div>
            <div className="text-sm text-nm-text-secondary mt-1">Average Rating</div>
          </div>
          <div className="bg-nm-card rounded-nm-card shadow-sm p-6">
            <div className="text-nm-orange text-3xl mb-2">🎥</div>
            <div className="text-3xl font-bold text-nm-text">
              {isLoading ? "-" : gamesAnalyzed}
            </div>
            <div className="text-sm text-nm-text-secondary mt-1">Games Analyzed</div>
          </div>
        </div>
      </div>

      <Link
        href="/training-plan"
        className="bg-nm-card rounded-nm-card shadow-sm px-6 py-5 flex items-center justify-between"
      >
        <span className="text-base font-medium text-nm-text">📋 Programme d'entraînement</span>
        <span className="text-nm-text-secondary text-lg">›</span>
      </Link>

      {/* Sport principal */}
      <div>
        <p className="text-base font-semibold text-nm-text mb-3">Sport principal</p>
        <div className="flex gap-3">
          {Object.entries(SPORT_LABEL).map(([value, label]) => (
            <button
              key={value}
              onClick={() => handleSportChange(value)}
              disabled={isUpdatingSport}
              className={`flex-1 py-4 rounded-nm-button text-base font-medium border transition-colors disabled:opacity-60 ${
                user.preferred_sport === value
                  ? "bg-nm-green-light border-nm-green text-nm-text"
                  : "border-nm-border text-nm-text-secondary bg-nm-card"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Settings */}
      <div>
        <p className="text-base font-semibold text-nm-text mb-3">Settings</p>
        <div className="flex flex-col gap-2">
          <button
            onClick={logout}
            className="bg-nm-card rounded-nm-card shadow-sm px-6 py-5 text-left text-nm-red text-base font-medium"
          >
            Se déconnecter
          </button>
        </div>
      </div>
    </div>
  );
}