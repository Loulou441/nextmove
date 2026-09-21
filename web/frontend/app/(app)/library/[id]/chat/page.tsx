"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, ChatTurn, MatchDetail, ApiError } from "@/lib/api";

function buildSuggestions(match: MatchDetail | null): string[] {
  if (!match) return [];
  const candidates: string[] = [];

  // Compétences : la plus faible, la deuxième plus faible, et la plus forte
  if (match.skills && match.skills.length > 0) {
    const sorted = [...match.skills].sort((a, b) => a.score - b.score);
    candidates.push(`Comment améliorer mon ${sorted[0].label.toLowerCase()} ?`);
    if (sorted.length > 1) {
      candidates.push(`Des conseils pour progresser en ${sorted[1].label.toLowerCase()} ?`);
    }
    const strongest = sorted[sorted.length - 1];
    candidates.push(`Comment exploiter encore plus mon point fort en ${strongest.label.toLowerCase()} ?`);
  }

  // Priorité tactique
  if (match.patterns_summary?.priority_level === "Élevée") {
    candidates.push("Quel est le point tactique le plus urgent à corriger ?");
  }

  // Ratio erreurs/winners
  if (match.errors != null && match.winners != null) {
    if (match.errors >= match.winners) {
      candidates.push("Pourquoi j'ai fait autant d'erreurs sur ce match ?");
    } else {
      candidates.push("Comment transformer encore plus d'occasions en points gagnants ?");
    }
  }

  // Insight tactique réel du pipeline
  const patternInsight = match.patterns_summary?.insights?.[0];
  if (patternInsight) {
    candidates.push(`Comment corriger ça : "${patternInsight}"`);
  }

  // Couverture de terrain
  if (match.coverage != null) {
    if (match.coverage < 50) {
      candidates.push("Comment mieux couvrir le terrain ?");
    } else {
      candidates.push("Comment utiliser ma bonne couverture pour prendre l'initiative ?");
    }
  }

  // Exposition en transition
  if (match.patterns_summary?.transition_risk_ratio != null && match.patterns_summary.transition_risk_ratio > 0.5) {
    candidates.push("Comment réduire mon exposition en phase de transition ?");
  }

  // Note globale
  if (match.rating != null && match.rating < 3.5) {
    candidates.push("Que dois-je travailler en priorité pour progresser rapidement ?");
  }

  // Questions génériques toujours pertinentes, pour garantir de la variété
  candidates.push("Donne-moi un conseil pour mon prochain match");
  candidates.push("Qu'est-ce que je devrais travailler en priorité ?");

  // Dédoublonnage (au cas où), mélange, et limite à 4
  const unique = Array.from(new Set(candidates));
  return unique.sort(() => Math.random() - 0.5).slice(0, 4);
}

export default function CoachChatPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();

  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!token || !id) return;
    api.getMatch(token, id).then(setMatch).catch(() => {});
  }, [token, id]);

  const suggestions = useMemo(() => buildSuggestions(match), [match]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  async function sendMessage(message: string) {
    if (!token || !id || !message.trim() || isSending) return;

    const newHistory: ChatTurn[] = [...history, { role: "user", text: message }];
    setHistory(newHistory);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const res = await api.chatWithCoach(token, id, message, history);
      setHistory([...newHistory, { role: "coach", text: res.reply }]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Le coach n'a pas pu répondre.");
      setHistory(history); // on retire le message utilisateur affiché en optimiste si l'appel échoue
    } finally {
      setIsSending(false);
    }
  }

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    sendMessage(input.trim());
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] md:h-[calc(100vh-3rem)] max-w-2xl">
      <div className="flex items-center gap-2 mb-4">
        <Link href={`/library/${id}`} className="text-nm-text-secondary text-sm">
          ← Retour
        </Link>
        <h1 className="text-xl font-bold text-nm-text ml-2">Coach IA</h1>
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pb-4">
        {history.length === 0 && (
          <>
            <div className="bg-nm-card rounded-nm-card shadow-sm p-4 text-sm text-nm-text-secondary">
              Pose une question sur ce match — technique, tactique, ou ce que tu peux travailler pour progresser.
            </div>
            {suggestions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {suggestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    disabled={isSending}
                    className="bg-nm-card border border-nm-border hover:bg-nm-bg text-nm-text text-sm rounded-nm-pill px-4 py-2 transition-colors disabled:opacity-60"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {history.map((turn, i) => (
          <div
            key={i}
            className={`max-w-[85%] px-4 py-2.5 rounded-nm-card text-sm ${
              turn.role === "user"
                ? "bg-nm-green text-white self-end rounded-br-md"
                : "bg-nm-card text-nm-text shadow-sm self-start rounded-bl-md"
            }`}
          >
            {turn.text}
          </div>
        ))}

        {isSending && (
          <div className="bg-nm-card shadow-sm self-start px-4 py-2.5 rounded-nm-card rounded-bl-md text-sm text-nm-text-secondary">
            Le coach réfléchit...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="bg-nm-card-orange border border-nm-card-orange-border rounded-nm-button px-4 py-2 text-sm text-nm-orange mb-2">
          {error}
        </div>
      )}

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Écris ton message..."
          className="flex-1 rounded-nm-button border border-nm-border px-4 py-2.5 text-sm text-nm-text bg-nm-card focus:outline-none focus:ring-2 focus:ring-nm-green"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="bg-nm-green hover:bg-nm-green-dark text-white font-semibold rounded-nm-button px-5 text-sm transition-colors disabled:opacity-60"
        >
          Envoyer
        </button>
      </form>
    </div>
  );
}