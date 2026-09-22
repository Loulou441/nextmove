"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, Match, ApiError } from "@/lib/api";
import ConfirmDialog from "@/components/ConfirmDialog";

const SPORT_EMOJI: Record<string, string> = {
  padel: "🥎",
  pickleball: "🏓",
  tennis: "🎾",
};

const STATUS_LABEL: Record<string, { text: string; className: string }> = {
  ready: { text: "Prêt", className: "bg-nm-status-ready-bg text-nm-status-ready-text" },
  pending: { text: "En attente", className: "bg-nm-status-pending-bg text-nm-status-pending-text" },
  processing: { text: "Analyse en cours", className: "bg-nm-status-pending-bg text-nm-status-pending-text" },
  failed: { text: "Échec", className: "bg-nm-card-orange text-nm-red" },
};

export default function LibraryPage() {
  const { token } = useAuth();
  const [matches, setMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sportFilter, setSportFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .getMatches(token)
      .then(setMatches)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erreur de chargement."))
      .finally(() => setIsLoading(false));
  }, [token]);

  function askDelete(e: React.MouseEvent, matchId: string) {
    e.preventDefault();
    e.stopPropagation();
    setPendingDeleteId(matchId);
  }

  async function confirmDelete() {
    if (!token || !pendingDeleteId) return;
    const matchId = pendingDeleteId;
    setPendingDeleteId(null);
    setDeletingId(matchId);
    try {
      await api.deleteMatch(token, matchId);
      setMatches((prev) => prev.filter((m) => m.id !== matchId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de supprimer ce match.");
    } finally {
      setDeletingId(null);
    }
  }

  const filteredMatches = useMemo(() => {
    return matches.filter((m) => {
      if (sportFilter !== "all" && m.sport !== sportFilter) return false;
      if (statusFilter !== "all" && m.status !== statusFilter) return false;
      if (search.trim() && !m.title.toLowerCase().includes(search.trim().toLowerCase())) return false;
      return true;
    });
  }, [matches, search, sportFilter, statusFilter]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-nm-text">Library</h1>
        <div className="flex gap-2">
          <Link
            href="/library/compare"
            className="bg-nm-card border border-nm-border hover:bg-nm-bg text-nm-text text-sm font-semibold rounded-nm-button px-4 py-2 transition-colors"
          >
            ⚖️ Comparer
          </Link>
          <Link
            href="/upload"
            className="bg-nm-green hover:bg-nm-green-dark text-white text-sm font-semibold rounded-nm-button px-4 py-2 transition-colors"
          >
            + Nouveau match
          </Link>
        </div>
      </div>

      {/* Recherche + filtres */}
      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher un match..."
          className="flex-1 rounded-nm-button border border-nm-border px-4 py-2 text-sm text-nm-text bg-nm-card focus:outline-none focus:ring-2 focus:ring-nm-green"
        />
        <select
          value={sportFilter}
          onChange={(e) => setSportFilter(e.target.value)}
          className="rounded-nm-button border border-nm-border px-3 py-2 text-sm text-nm-text bg-nm-card focus:outline-none focus:ring-2 focus:ring-nm-green"
        >
          <option value="all">Tous les sports</option>
          <option value="padel">🥎 Padel</option>
          <option value="pickleball">🏓 Pickleball</option>
          <option value="tennis">🎾 Tennis</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-nm-button border border-nm-border px-3 py-2 text-sm text-nm-text bg-nm-card focus:outline-none focus:ring-2 focus:ring-nm-green"
        >
          <option value="all">Tous les statuts</option>
          <option value="ready">Prêt</option>
          <option value="pending">En attente</option>
          <option value="processing">Analyse en cours</option>
          <option value="failed">Échec</option>
        </select>
      </div>

      {isLoading && <p className="text-nm-text-secondary text-sm">Chargement...</p>}

      {error && (
        <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-3 text-sm text-nm-orange mb-4">
          {error}
        </div>
      )}

      {!isLoading && !error && matches.length === 0 && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
          <p className="text-nm-text-secondary text-sm">
            Aucun match pour l'instant. Importe ta première vidéo pour commencer.
          </p>
        </div>
      )}

      {!isLoading && matches.length > 0 && filteredMatches.length === 0 && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
          <p className="text-nm-text-secondary text-sm">Aucun match ne correspond à ta recherche.</p>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {filteredMatches.map((match) => {
          const status = STATUS_LABEL[match.status] ?? STATUS_LABEL.pending;
          return (
            <Link
              key={match.id}
              href={`/library/${match.id}`}
              className="bg-nm-card rounded-nm-card shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow group"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{SPORT_EMOJI[match.sport] ?? "🏆"}</span>
                <div>
                  <p className="font-semibold text-nm-text text-sm">{match.title}</p>
                  <p className="text-nm-text-secondary text-xs">
                    {match.match_date ? new Date(match.match_date).toLocaleDateString("fr-FR") : ""}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {match.rating != null && (
                  <span className="text-nm-text font-semibold text-sm">⭐ {match.rating}</span>
                )}
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-nm-pill ${status.className}`}>
                  {status.text}
                </span>
                <button
                  onClick={(e) => askDelete(e, match.id)}
                  disabled={deletingId === match.id}
                  className="opacity-0 group-hover:opacity-100 text-nm-text-secondary hover:text-nm-red transition-opacity disabled:opacity-60 text-sm px-1"
                  title="Supprimer ce match"
                >
                  {deletingId === match.id ? "..." : "🗑️"}
                </button>
              </div>
            </Link>
          );
        })}
      </div>

      <ConfirmDialog
        open={pendingDeleteId !== null}
        title="Supprimer ce match ?"
        message="Cette action est irréversible. Le match, ses événements et ses analyses seront définitivement supprimés."
        confirmLabel="Supprimer"
        isDangerous
        onConfirm={confirmDelete}
        onCancel={() => setPendingDeleteId(null)}
      />
    </div>
  );
}