"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, MatchDetail, ApiError } from "@/lib/api";

const COLOR_CLASS: Record<string, string> = {
  green: "text-nm-green",
  blue: "text-nm-blue",
  orange: "text-nm-orange",
  red: "text-nm-red",
};

const FILL_COLOR: Record<string, string> = {
  green: "#34C759",
  blue: "#007AFF",
  orange: "#FF9500",
  red: "#FF3B30",
};

const POLL_INTERVAL_MS = 4000;

export default function MatchDashboardPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStartingAnalysis, setIsStartingAnalysis] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!token || !id) return;

    let cancelled = false;

    function fetchMatch() {
      api
        .getMatch(token!, id)
        .then((data) => {
          if (cancelled) return;
          setMatch(data);
          setError(null);
          // Dès que l'analyse est terminée (succès ou échec), on arrête de sonder.
          if (data.status !== "processing" && intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err instanceof ApiError ? err.message : "Erreur de chargement.");
          }
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    }

    fetchMatch();
    intervalRef.current = setInterval(fetchMatch, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [token, id]);

  async function handleStartAnalysis() {
    if (!token || !id) return;
    setIsStartingAnalysis(true);
    try {
      const updated = await api.analyzeMatch(token, id);
      setMatch(updated);
      // Relance le polling maintenant que le statut est passé à "processing".
      if (!intervalRef.current) {
        intervalRef.current = setInterval(() => {
          api.getMatch(token, id).then((data) => {
            setMatch(data);
            if (data.status !== "processing" && intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          });
        }, POLL_INTERVAL_MS);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de démarrer l'analyse.");
    } finally {
      setIsStartingAnalysis(false);
    }
  }

  if (isLoading) {
    return <p className="text-nm-text-secondary text-sm">Chargement...</p>;
  }

  if (error || !match) {
    return (
      <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-3 text-sm text-nm-orange">
        {error ?? "Match introuvable."}
      </div>
    );
  }

  if (match.status === "processing") {
    return (
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
        <div className="w-6 h-6 border-2 border-nm-green border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-nm-text font-medium mb-1">Analyse en cours...</p>
        <p className="text-nm-text-secondary text-sm">
          Cette page se met à jour automatiquement, pas besoin de recharger.
        </p>
      </div>
    );
  }

  if (match.status === "pending") {
    return (
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
        <p className="text-nm-text font-medium mb-1">Vidéo importée, analyse pas encore lancée</p>
        <p className="text-nm-text-secondary text-sm mb-4">
          Clique ci-dessous pour démarrer l'analyse CV de ce match.
        </p>
        <button
          onClick={handleStartAnalysis}
          disabled={isStartingAnalysis}
          className="bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button px-6 py-2.5 text-sm transition-colors disabled:opacity-60"
        >
          {isStartingAnalysis ? "Démarrage..." : "Lancer l'analyse"}
        </button>
      </div>
    );
  }

  if (match.status === "failed") {
    return (
      <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-3 text-sm text-nm-orange">
        {match.insights?.[0]?.text ?? "L'analyse de ce match a échoué."}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nm-text">{match.title}</h1>
          <p className="text-nm-text-secondary text-sm">
            {match.match_date ? new Date(match.match_date).toLocaleDateString("fr-FR") : ""}
          </p>
        </div>
        <div className="flex gap-2 no-print">
          <button
            onClick={() => window.print()}
            className="bg-nm-card border border-nm-border hover:bg-nm-bg text-nm-text text-sm font-semibold rounded-nm-button px-4 py-2 transition-colors shrink-0"
          >
            📄 Export PDF
          </button>
          <Link
            href={`/library/${match.id}/chat`}
            className="bg-nm-green hover:bg-nm-green-dark text-white text-sm font-semibold rounded-nm-button px-4 py-2 transition-colors shrink-0"
          >
            💬 Coach
          </Link>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard icon="⭐" value={match.rating ?? "-"} label="Note" />
        <KpiCard icon="🔁" value={match.rallies ?? "-"} label="Rallies" />
        <KpiCard icon="🏆" value={match.winners ?? "-"} label="Winners" />
        <KpiCard icon="❌" value={match.errors ?? "-"} label="Erreurs" />
      </div>

      {match.coverage != null && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
          <p className="text-sm font-medium text-nm-text mb-1">Couverture de terrain</p>
          <div className="h-2 bg-nm-border rounded-full overflow-hidden">
            <div
              className="h-full bg-nm-green rounded-full"
              style={{ width: `${match.coverage}%` }}
            />
          </div>
          <p className="text-xs text-nm-text-secondary mt-1">{match.coverage}%</p>
        </div>
      )}

      {/* Skills */}
      {match.skills && match.skills.length > 0 && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
          <p className="text-sm font-semibold text-nm-text mb-3">Compétences</p>
          <div className="flex flex-col gap-3">
            {match.skills.map((skill) => (
              <div key={skill.label}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-nm-text">
                    {skill.icon} {skill.label}
                  </span>
                  <span className={`text-sm font-semibold ${COLOR_CLASS[skill.color] ?? "text-nm-green"}`}>
                    {skill.score}
                  </span>
                </div>
                <div className="h-2 bg-nm-border rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(skill.score / 5) * 100}%`,
                      background: FILL_COLOR[skill.color] ?? "#34C759",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Highlights */}
      {match.highlights && match.highlights.length > 0 && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
          <p className="text-sm font-semibold text-nm-text mb-2">Temps forts</p>
          <div className="flex flex-col">
            {match.highlights.map((h, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2.5 border-b border-nm-bg last:border-none"
              >
                <div>
                  <p className="text-sm font-medium text-nm-text">{h.title}</p>
                  <p className="text-xs text-nm-text-secondary">{h.time}</p>
                </div>
                <span className="text-[11px] font-semibold px-2.5 py-1 rounded-nm-pill bg-nm-tag-winner-bg text-nm-tag-winner-text">
                  {h.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Patterns tactiques */}
      {match.patterns_summary && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-nm-text">Analyse tactique</p>
            {match.patterns_summary.priority_level && (
              <span
                className={`text-[11px] font-semibold px-2.5 py-1 rounded-nm-pill ${
                  match.patterns_summary.priority_level === "Élevée"
                    ? "bg-nm-card-orange text-nm-orange"
                    : "bg-nm-green-light text-nm-green"
                }`}
              >
                Priorité {match.patterns_summary.priority_level}
              </span>
            )}
          </div>

          {match.patterns_summary.insights && match.patterns_summary.insights.length > 0 && (
            <div className="flex flex-col gap-2 mb-4">
              {match.patterns_summary.insights.map((text, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-nm-text">
                  <span className="w-2 h-2 rounded-full bg-nm-orange mt-1.5 shrink-0" />
                  {text}
                </div>
              ))}
            </div>
          )}

          {match.patterns_summary.transition_risk_ratio != null && (
            <div className="mb-4">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-nm-text">Exposition en transition</span>
                <span className="text-sm font-semibold text-nm-orange">
                  {Math.round(match.patterns_summary.transition_risk_ratio * 100)}%
                </span>
              </div>
              <div className="h-2 bg-nm-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-nm-orange rounded-full"
                  style={{ width: `${match.patterns_summary.transition_risk_ratio * 100}%` }}
                />
              </div>
            </div>
          )}

          {match.patterns_summary.phase_distribution && (
            <DistributionList
              title="Répartition par phase de jeu"
              data={match.patterns_summary.phase_distribution}
            />
          )}

          {match.patterns_summary.zone_distribution && (
            <DistributionList
              title="Répartition par zone du terrain"
              data={match.patterns_summary.zone_distribution}
            />
          )}
        </div>
      )}

      {/* Insights */}
      {match.insights && match.insights.length > 0 && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
          <p className="text-sm font-semibold text-nm-text mb-2">Analyse</p>
          <div className="flex flex-col gap-2">
            {match.insights.map((insight, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-nm-text">
                <span
                  className="w-2 h-2 rounded-full mt-1.5 shrink-0"
                  style={{ background: insight.color }}
                />
                {insight.text}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KpiCard({ icon, value, label }: { icon: string; value: string | number; label: string }) {
  return (
    <div className="bg-nm-bg rounded-[14px] p-4 text-center">
      <div className="text-xl mb-1">{icon}</div>
      <div className="text-xl font-bold text-nm-text">{value}</div>
      <div className="text-xs text-nm-text-secondary">{label}</div>
    </div>
  );
}

function DistributionList({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  if (total === 0) return null;

  return (
    <div className="mb-3 last:mb-0">
      <p className="text-xs font-medium text-nm-text-secondary mb-2">{title}</p>
      <div className="flex flex-col gap-2">
        {entries.map(([label, count]) => {
          const pct = Math.round((count / total) * 100);
          return (
            <div key={label}>
              <div className="flex justify-between text-xs text-nm-text mb-0.5">
                <span>{label}</span>
                <span className="text-nm-text-secondary">{pct}%</span>
              </div>
              <div className="h-1.5 bg-nm-border rounded-full overflow-hidden">
                <div className="h-full bg-nm-blue rounded-full" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}