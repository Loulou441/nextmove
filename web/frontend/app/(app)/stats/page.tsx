"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";
import { api, Match } from "@/lib/api";

const SPORT_LABEL: Record<string, string> = {
  padel: "🥎 Padel",
  pickleball: "🏓 Pickleball",
  tennis: "🎾 Tennis",
};

const ZONE_COLORS = ["#34C759", "#007AFF", "#FF9500", "#FF3B30", "#AF52DE"];
const PERIODS = [
  { key: "all", label: "Tout" },
  { key: "10", label: "10 derniers" },
  { key: "5", label: "5 derniers" },
];

interface TimelinePoint {
  match_id: string;
  title: string;
  sport: string;
  date: string;
  rating: number | null;
  coverage: number | null;
  rallies: number | null;
  winners: number | null;
  errors: number | null;
}

interface AggregateStats {
  timeline: TimelinePoint[];
  avg_skills: { label: string; score: number }[];
  phase_distribution: Record<string, number>;
  zone_distribution: Record<string, number>;
  summary: {
    total_matches: number;
    avg_rating: number | null;
    best_match: string | null;
  };
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) return null;
  const point = payload[0].payload;
  return (
    <div className="bg-white rounded-nm-button border border-nm-border px-3 py-2 shadow-md text-sm">
      <p className="font-semibold text-nm-text">{point.title}</p>
      <p className="text-nm-text-secondary text-xs mb-1">{point.dateLabel}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} className="text-nm-text">{p.name} : <span className="font-semibold">{p.value}</span></p>
      ))}
      {point.match_id && <p className="text-nm-green text-xs mt-1">Cliquer pour ouvrir →</p>}
    </div>
  );
}

function TrendBadge({ current, previous }: { current: number | null; previous: number | null }) {
  if (current == null || previous == null || previous === 0) return null;
  const diff = current - previous;
  if (Math.abs(diff) < 0.05) {
    return <span className="text-xs text-nm-text-secondary">= stable</span>;
  }
  const isUp = diff > 0;
  return (
    <span className={`text-xs font-semibold ${isUp ? "text-nm-green" : "text-nm-red"}`}>
      {isUp ? "↗" : "↘"} {isUp ? "+" : ""}{diff.toFixed(1)}
    </span>
  );
}

export default function StatsPage() {
  const router = useRouter();
  const [allMatches, setAllMatches] = useState<Match[]>([]);
  const [stats, setStats] = useState<AggregateStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sportFilter, setSportFilter] = useState<string>("all");
  const [period, setPeriod] = useState<string>("all");

  useEffect(() => {
    api.getMatches().then(setAllMatches).catch(() => {});
  }, []);

  useEffect(() => {
    setIsLoading(true);
    const path = sportFilter === "all" ? "" : `?sport=${sportFilter}`;
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/matches/stats/aggregate${path}`, { credentials: "include" })
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setIsLoading(false));
  }, [sportFilter]);

  const availableSports = useMemo(() => {
    return Array.from(new Set(allMatches.map((m) => m.sport)));
  }, [allMatches]);

  const filteredTimeline = useMemo(() => {
    if (!stats) return [];
    if (period === "all") return stats.timeline;
    const n = parseInt(period, 10);
    return stats.timeline.slice(-n);
  }, [stats, period]);

  // index numérique unique et croissant : évite que Recharts regroupe des
  // points qui partagent la même date affichée (plusieurs matchs le même
  // jour), ce qui faisait apparaître le mauvais titre au survol.
  const chartData = useMemo(() => {
    return filteredTimeline.map((m, i) => ({
      ...m,
      index: i,
      dateLabel: new Date(m.date).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit" }),
    }));
  }, [filteredTimeline]);

  const phaseData = useMemo(() => {
    if (!stats) return [];
    const total = Object.values(stats.phase_distribution).reduce((a, b) => a + b, 0) || 1;
    return Object.entries(stats.phase_distribution).map(([name, count]) => ({
      name, pct: Math.round((count / total) * 100),
    }));
  }, [stats]);

  const zoneData = useMemo(() => {
    if (!stats) return [];
    const total = Object.values(stats.zone_distribution).reduce((a, b) => a + b, 0) || 1;
    return Object.entries(stats.zone_distribution).map(([name, count]) => ({
      name, pct: Math.round((count / total) * 100),
    }));
  }, [stats]);

  // Tendance : moyenne de la 2e moitié de la période contre la 1re moitié.
  const trend = useMemo(() => {
    if (filteredTimeline.length < 2) return { current: null, previous: null };
    const mid = Math.floor(filteredTimeline.length / 2);
    const firstHalf = filteredTimeline.slice(0, mid);
    const secondHalf = filteredTimeline.slice(mid);
    const avg = (arr: TimelinePoint[]) => {
      const valid = arr.map((m) => m.rating).filter((r): r is number => r != null);
      return valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : null;
    };
    return { current: avg(secondHalf), previous: avg(firstHalf) };
  }, [filteredTimeline]);

  const hasEnoughData = filteredTimeline.length >= 2;

  function goToMatch(data: any) {
    if (data?.activePayload?.[0]?.payload?.match_id) {
      router.push(`/library/${data.activePayload[0].payload.match_id}`);
    }
  }

  return (
    <div className="max-w-4xl flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-nm-text mb-1">Évolution</h1>
        <p className="text-nm-text-secondary text-sm">
          Ta progression au fil de tes matchs analysés.
        </p>
      </div>

      {/* Filtres — toujours visibles */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSportFilter("all")}
            className={`px-3 py-1.5 rounded-nm-pill text-sm font-medium border transition-colors ${
              sportFilter === "all"
                ? "bg-nm-green-light border-nm-green text-nm-text"
                : "border-nm-border text-nm-text-secondary bg-nm-card hover:bg-nm-bg"
            }`}
          >
            Tous les sports
          </button>
          {availableSports.map((sport) => (
            <button
              key={sport}
              onClick={() => setSportFilter(sport)}
              className={`px-3 py-1.5 rounded-nm-pill text-sm font-medium border transition-colors ${
                sportFilter === sport
                  ? "bg-nm-green-light border-nm-green text-nm-text"
                  : "border-nm-border text-nm-text-secondary bg-nm-card hover:bg-nm-bg"
              }`}
            >
              {SPORT_LABEL[sport] ?? sport}
            </button>
          ))}
        </div>

        <div className="flex gap-1 bg-nm-bg rounded-nm-pill p-1 w-fit">
          {PERIODS.map((p) => (
            <button
              key={p.key}
              onClick={() => setPeriod(p.key)}
              className={`px-3 py-1 rounded-nm-pill text-xs font-medium transition-colors ${
                period === p.key ? "bg-nm-card text-nm-text shadow-sm" : "text-nm-text-secondary"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <p className="text-nm-text-secondary text-sm">Chargement...</p>}

      {!isLoading && stats && (
        <>
          {/* Cartes de synthèse */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
              <p className="text-2xl font-bold text-nm-text">{filteredTimeline.length}</p>
              <p className="text-xs text-nm-text-secondary mt-1">Matchs sur la période</p>
            </div>
            <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-bold text-nm-text">{stats.summary.avg_rating ?? "-"}</p>
                <TrendBadge current={trend.current} previous={trend.previous} />
              </div>
              <p className="text-xs text-nm-text-secondary mt-1">Note moyenne</p>
            </div>
            <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
              <p className="text-sm font-bold text-nm-text truncate">{stats.summary.best_match ?? "-"}</p>
              <p className="text-xs text-nm-text-secondary mt-1">Meilleur match</p>
            </div>
          </div>

          {!hasEnoughData && (
            <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
              <p className="text-nm-text-secondary text-sm">
                Il te faut au moins 2 matchs analysés sur cette période pour voir des graphiques.
              </p>
            </div>
          )}

          {hasEnoughData && (
            <>
              <p className="text-xs text-nm-text-secondary -mb-2">Clique sur un point pour ouvrir le match correspondant.</p>

              {/* Note */}
              <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
                <p className="text-sm font-semibold text-nm-text mb-4">Note (/5)</p>
                <div style={{ width: "100%", height: 240 }}>
                  <ResponsiveContainer>
                    <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }} onClick={goToMatch}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E5EA" />
                      <XAxis
                        dataKey="index"
                        tick={{ fontSize: 12, fill: "#8E8E93" }}
                        tickFormatter={(i) => chartData[i]?.dateLabel ?? ""}
                      />
                      <YAxis domain={[0, 5]} tick={{ fontSize: 12, fill: "#8E8E93" }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line
                        type="monotone" dataKey="rating" name="Note" stroke="#34C759" strokeWidth={2}
                        dot={{ r: 4, cursor: "pointer" }} activeDot={{ r: 6, cursor: "pointer" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Couverture */}
              <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
                <p className="text-sm font-semibold text-nm-text mb-4">Couverture de terrain (%)</p>
                <div style={{ width: "100%", height: 240 }}>
                  <ResponsiveContainer>
                    <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }} onClick={goToMatch}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E5EA" />
                      <XAxis
                        dataKey="index"
                        tick={{ fontSize: 12, fill: "#8E8E93" }}
                        tickFormatter={(i) => chartData[i]?.dateLabel ?? ""}
                      />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: "#8E8E93" }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line
                        type="monotone" dataKey="coverage" name="Couverture" stroke="#007AFF" strokeWidth={2}
                        dot={{ r: 4, cursor: "pointer" }} activeDot={{ r: 6, cursor: "pointer" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Winners vs erreurs */}
              <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
                <p className="text-sm font-semibold text-nm-text mb-4">Winners vs erreurs</p>
                <div style={{ width: "100%", height: 240 }}>
                  <ResponsiveContainer>
                    <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }} onClick={goToMatch}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E5EA" />
                      <XAxis
                        dataKey="index"
                        tick={{ fontSize: 12, fill: "#8E8E93" }}
                        tickFormatter={(i) => chartData[i]?.dateLabel ?? ""}
                      />
                      <YAxis tick={{ fontSize: 12, fill: "#8E8E93" }} allowDecimals={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="winners" name="Winners" fill="#34C759" radius={[4, 4, 0, 0]} cursor="pointer" />
                      <Bar dataKey="errors" name="Erreurs" fill="#FF3B30" radius={[4, 4, 0, 0]} cursor="pointer" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}

          {/* Compétences moyennes */}
          {stats.avg_skills.length > 0 && (
            <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
              <p className="text-sm font-semibold text-nm-text mb-4">Compétences moyennes sur la période</p>
              <div style={{ width: "100%", height: Math.max(200, stats.avg_skills.length * 42) }}>
                <ResponsiveContainer>
                  <BarChart data={stats.avg_skills} layout="vertical" margin={{ top: 5, right: 24, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E5EA" horizontal={false} />
                    <XAxis type="number" domain={[0, 5]} tick={{ fontSize: 12, fill: "#8E8E93" }} />
                    <YAxis type="category" dataKey="label" tick={{ fontSize: 12, fill: "#1C1C1E" }} width={100} />
                    <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #E5E5EA", fontSize: 13 }} />
                    <Bar dataKey="score" name="Score" radius={[0, 4, 4, 0]}>
                      {stats.avg_skills.map((s, i) => (
                        <Cell key={i} fill={s.score >= 4 ? "#34C759" : s.score >= 3 ? "#007AFF" : "#FF9500"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Répartition phase / zone */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {phaseData.length > 0 && (
              <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
                <p className="text-sm font-semibold text-nm-text mb-4">Phases de jeu (cumulé)</p>
                <div style={{ width: "100%", height: 200 }}>
                  <ResponsiveContainer>
                    <BarChart data={phaseData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#8E8E93" }} />
                      <YAxis tick={{ fontSize: 11, fill: "#8E8E93" }} unit="%" />
                      <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #E5E5EA", fontSize: 13 }} />
                      <Bar dataKey="pct" name="Part" radius={[4, 4, 0, 0]}>
                        {phaseData.map((_, i) => <Cell key={i} fill={ZONE_COLORS[i % ZONE_COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {zoneData.length > 0 && (
              <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
                <p className="text-sm font-semibold text-nm-text mb-4">Zones du terrain (cumulé)</p>
                <div style={{ width: "100%", height: 200 }}>
                  <ResponsiveContainer>
                    <BarChart data={zoneData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#8E8E93" }} />
                      <YAxis tick={{ fontSize: 11, fill: "#8E8E93" }} unit="%" />
                      <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #E5E5EA", fontSize: 13 }} />
                      <Bar dataKey="pct" name="Part" radius={[4, 4, 0, 0]}>
                        {zoneData.map((_, i) => <Cell key={i} fill={ZONE_COLORS[i % ZONE_COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}