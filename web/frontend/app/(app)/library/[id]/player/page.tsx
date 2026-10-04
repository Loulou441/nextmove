"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, MatchDetail, ApiError } from "@/lib/api";

export default function PlayerSelectionPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    api
      .getMatch(id)
      .then(setMatch)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erreur de chargement."));
  }, [id]);

  async function choose(index: number | null) {
    setSaving(true);
    setError(null);
    try {
      await api.selectPlayer(id, index);
      router.push(`/library/${id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'enregistrer ton choix.");
      setSaving(false);
    }
  }

  if (error && !match) {
    return (
      <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-3 text-sm text-nm-orange">
        {error}
      </div>
    );
  }

  if (!match) {
    return <p className="text-nm-text-secondary text-sm">Chargement...</p>;
  }

  const players = match.players ?? [];

  if (players.length < 2) {
    return (
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
        <p className="text-nm-text font-medium mb-3">Aucun choix de joueur disponible pour ce match.</p>
        <Link href={`/library/${id}`} className="text-nm-green text-sm font-semibold hover:underline">
          Retour au match
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold text-nm-text">Qui es-tu sur la vidéo ?</h1>
        <p className="text-nm-text-secondary text-sm">
          Choisis ton joueur : ta couverture du terrain, ton déplacement et ta note seront calculés à partir de tes
          propres positions.
        </p>
      </div>

      {error && (
        <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-2.5 text-sm text-nm-orange">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {players.map((p) => {
          const isSelected = match.selected_player_index === p.index;
          return (
            <div
              key={p.index}
              className={`bg-nm-card rounded-nm-card shadow-sm p-3 flex flex-col items-center gap-2 border-2 ${
                isSelected ? "border-nm-green" : "border-transparent"
              }`}
            >
              {p.thumbnail ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={p.thumbnail} alt={p.label} className="w-full aspect-[3/4] object-cover rounded-nm-button bg-nm-bg" />
              ) : (
                <div className="w-full aspect-[3/4] rounded-nm-button bg-nm-bg flex items-center justify-center text-nm-text-secondary text-2xl">
                  {p.index}
                </div>
              )}
              <p className="text-sm font-semibold text-nm-text text-center">{p.label}</p>
              {p.is_likely_user && <span className="text-xs text-nm-green">Joueur probable</span>}
              <button
                onClick={() => choose(p.index)}
                disabled={saving}
                className="w-full bg-nm-green hover:bg-nm-green-dark text-white text-sm font-semibold rounded-nm-button py-2 transition-colors disabled:opacity-60"
              >
                {isSelected ? "Ton joueur" : "C'est moi"}
              </button>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={() => choose(null)}
          disabled={saving}
          className="text-sm text-nm-text-secondary hover:underline disabled:opacity-60"
        >
          Voir le match entier
        </button>
        <Link href={`/library/${id}`} className="text-sm text-nm-green font-semibold hover:underline">
          Retour au match
        </Link>
      </div>
    </div>
  );
}