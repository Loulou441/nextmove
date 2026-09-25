"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { api, Match } from "@/lib/api";

export default function StatsPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .getMatches()
      .then(setMatches)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const readyMatches = matches
    .filter((m) => m.status === "ready" && m.rating != null)
    .sort((a, b) => new Date(a.match_date ?? a.created_at).getTime() - new Date(b.match_date ?? b.created_at).getTime());

  const chartData = readyMatches.map((m) => ({
    name: m.match_date ? new Date(m.match_date).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" }) : "",
    title: m.title,
    rating: m.rating,
    coverage: m.coverage,
  }));

  return (
    <div className="max-w-3xl flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold text-nm-text mb-1">Évolution</h1>
        <p className="text-nm-text-secondary text-sm">
          Ta progression au fil de tes matchs analysés.
        </p>
      </div>

      {isLoading && <p className="text-nm-text-secondary text-sm">Chargement...</p>}

      {!isLoading && readyMatches.length < 2 && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center">
          <p className="text-nm-text-secondary text-sm">
            Il te faut au moins 2 matchs analysés pour voir une évolution.
          </p>
        </div>
      )}

      {!isLoading && readyMatches.length >= 2 && (
        <div className="bg-nm-card rounded-nm-card shadow-sm p-4">
          <p className="text-sm font-semibold text-nm-text mb-4">Note et couverture de terrain</p>
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5EA" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#8E8E93" }} />
                <YAxis yAxisId="left" domain={[0, 5]} tick={{ fontSize: 12, fill: "#8E8E93" }} />
                <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 12, fill: "#8E8E93" }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #E5E5EA", fontSize: 13 }}
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.title ?? ""}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="rating"
                  name="Note (/5)"
                  stroke="#34C759"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="coverage"
                  name="Couverture (%)"
                  stroke="#007AFF"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}