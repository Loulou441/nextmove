"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Match, MatchDetail } from "@/lib/api";

const ROWS: { label: string; key: keyof MatchDetail; suffix?: string }[] = [
  { label: "Note", key: "rating" },
  { label: "Rallies", key: "rallies" },
  { label: "Winners", key: "winners" },
  { label: "Erreurs", key: "errors" },
  { label: "Couverture de terrain", key: "coverage", suffix: "%" },
];

export default function ComparePage() {
  const { token } = useAuth();
  const [matches, setMatches] = useState<Match[]>([]);
  const [leftId, setLeftId] = useState<string>("");
  const [rightId, setRightId] = useState<string>("");
  const [left, setLeft] = useState<MatchDetail | null>(null);
  const [right, setRight] = useState<MatchDetail | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getMatches(token).then((all) => {
      const ready = all.filter((m) => m.status === "ready");
      setMatches(ready);
      if (ready.length >= 2) {
        setLeftId(ready[0].id);
        setRightId(ready[1].id);
      }
    });
  }, [token]);

  useEffect(() => {
    if (!token || !leftId) return;
    api.getMatch(token, leftId).then(setLeft);
  }, [token, leftId]);

  useEffect(() => {
    if (!token || !rightId) return;
    api.getMatch(token, rightId).then(setRight);
  }, [token, rightId]);

  if (matches.length < 2) {
    return (
      <div className="bg-nm-card rounded-nm-card shadow-sm p-8 text-center max-w-lg">
        <p className="text-nm-text-secondary text-sm">
          Il te faut au moins 2 matchs analysés pour faire une comparaison.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-nm-text">Comparer deux matchs</h1>

      <div className="grid grid-cols-2 gap-3">
        <MatchSelect matches={matches} value={leftId} onChange={setLeftId} exclude={rightId} />
        <MatchSelect matches={matches} value={rightId} onChange={setRightId} exclude={leftId} />
      </div>

      {left && right && (
        <div className="bg-nm-card rounded-nm-card shadow-sm overflow-hidden">
          <div className="grid grid-cols-3 border-b border-nm-bg px-4 py-3">
            <span className="text-xs font-semibold text-nm-text-secondary">Métrique</span>
            <span className="text-xs font-semibold text-nm-text text-center truncate">{left.title}</span>
            <span className="text-xs font-semibold text-nm-text text-center truncate">{right.title}</span>
          </div>

          {ROWS.map((row) => {
            const leftVal = left[row.key] as number | null;
            const rightVal = right[row.key] as number | null;
            const leftBetter = leftVal != null && rightVal != null && leftVal > rightVal;
            const rightBetter = leftVal != null && rightVal != null && rightVal > leftVal;

            return (
              <div
                key={row.label}
                className="grid grid-cols-3 items-center px-4 py-3 border-b border-nm-bg last:border-none"
              >
                <span className="text-sm text-nm-text-secondary">{row.label}</span>
                <span
                  className={`text-sm text-center font-semibold ${
                    leftBetter ? "text-nm-green" : "text-nm-text"
                  }`}
                >
                  {leftVal ?? "-"}
                  {row.suffix ?? ""}
                </span>
                <span
                  className={`text-sm text-center font-semibold ${
                    rightBetter ? "text-nm-green" : "text-nm-text"
                  }`}
                >
                  {rightVal ?? "-"}
                  {row.suffix ?? ""}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MatchSelect({
  matches,
  value,
  onChange,
  exclude,
}: {
  matches: Match[];
  value: string;
  onChange: (id: string) => void;
  exclude: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-nm-button border border-nm-border px-3 py-2.5 text-sm text-nm-text bg-nm-card focus:outline-none focus:ring-2 focus:ring-nm-green"
    >
      {matches
        .filter((m) => m.id !== exclude)
        .map((m) => (
          <option key={m.id} value={m.id}>
            {m.title} — {m.match_date ? new Date(m.match_date).toLocaleDateString("fr-FR") : ""}
          </option>
        ))}
    </select>
  );
}