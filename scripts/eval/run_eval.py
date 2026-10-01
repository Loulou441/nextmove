"""
Kit d'évaluation des coachs NextMove (RAG, modérateur, comparaison avec/sans RAG).

Depuis la racine du dépôt, environnement installé :

    python scripts/eval/run_eval.py check                 # valide les jeux de test (hors-ligne)
    python scripts/eval/run_eval.py rag                   # métriques du RAG (modèle d'embedding réel)
    python scripts/eval/run_eval.py moderator             # précision du modérateur (GROQ_API_KEY)
    python scripts/eval/run_eval.py ab --n 12             # coach avec RAG vs sans RAG, juge LLM (GROQ_API_KEY)

Chaque commande écrit un JSON dans scripts/eval/results/ (à joindre au dossier).
"""
import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"
AGENTS = ROOT / "backend" / "agents"

SPORTS = {
    "padel": ("agentpadel", "padel", "agent_recommendation_padel", "PadelCoachAI"),
    "tennis": ("agenttennis", "tennis", "agent_recommendation_tennis", "TennisCoachAI"),
    "pickleball": ("agentpickelball", "pickelball", "agent_recommendation_pickelball", "PickelballCoachAI"),
}


def load_gold():
    gold = json.loads((EVAL_DIR / "gold_rag.json").read_text(encoding="utf-8"))
    return {s: gold[s] for s in SPORTS}


def kb_path(sport):
    folder, suffix, _, _ = SPORTS[sport]
    return AGENTS / folder / f"knowledge_{suffix}.json"


def save(name, payload):
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print(f"→ résultats écrits dans {shown}")


def wilson(k, n, z=1.96):
    """Intervalle de confiance de Wilson à 95 % pour une proportion k/n."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    marge = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - marge), min(1.0, centre + marge))


def fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.0%} (IC95 % : {lo:.0%}–{hi:.0%})" if n else "n/a"


# --------------------------------------------------------------------------- check
def cmd_check(_args):
    ok = True
    gold = load_gold()
    for sport, items in gold.items():
        ids = {d["id"] for d in json.loads(kb_path(sport).read_text(encoding="utf-8"))}
        for it in items:
            unknown = [i for i in it["expected_ids"] if i not in ids]
            if unknown or not it["expected_ids"]:
                ok = False
                print(f"[{sport}] ids inconnus/absents pour « {it['query'][:50]}… » : {unknown}")
    cases = json.loads((EVAL_DIR / "moderator_cases.json").read_text(encoding="utf-8"))["cases"]
    n_legit = sum(not c["is_prompt_injection"] and not c["off_topic"] for c in cases)
    print(f"RAG : {sum(len(v) for v in gold.values())} requêtes annotées | modérateur : {len(cases)} cas ({n_legit} légitimes)")
    print("OK" if ok else "ERREURS dans le jeu de test")
    sys.exit(0 if ok else 1)


# --------------------------------------------------------------------------- rag
def evaluate_rag(get_kb=None, ks=(1, 3, 5)):
    from backend.agents.agentmanager.rag import get_knowledge_base

    get_kb = get_kb or get_knowledge_base
    per_sport, all_rr, all_hits = {}, [], {k: [] for k in ks}
    for sport, items in load_gold().items():
        kb = get_kb(sport, kb_path(sport))
        hits, rr, misses = {k: 0 for k in ks}, [], []
        for it in items:
            ranked = [r["id"] for r in kb.retrieve(it["query"], k=max(ks))]
            expected = set(it["expected_ids"])
            rank = next((i + 1 for i, rid in enumerate(ranked) if rid in expected), None)
            rr.append(1 / rank if rank else 0.0)
            for k in ks:
                hits[k] += rank is not None and rank <= k
                all_hits[k].append(rank is not None and rank <= k)
            if rank is None or rank > 3:
                misses.append({"query": it["query"], "attendus": it["expected_ids"], "top3": ranked[:3]})
        all_rr += rr
        per_sport[sport] = {
            "n": len(items),
            **{f"hit@{k}": hits[k] for k in ks},
            "mrr": round(sum(rr) / len(rr), 3),
            "hors_top3": misses,
        }
    total = {
        "n": len(all_rr),
        **{f"hit@{k}": sum(all_hits[k]) for k in ks},
        "mrr": round(sum(all_rr) / len(all_rr), 3),
    }
    return {"par_sport": per_sport, "global": total}


def cmd_rag(_args):
    res = evaluate_rag()
    for sport, r in res["par_sport"].items():
        print(f"[{sport}] hit@1 {fmt(r['hit@1'], r['n'])} | hit@3 {fmt(r['hit@3'], r['n'])} | MRR {r['mrr']}")
        for m in r["hors_top3"]:
            print(f"    raté : « {m['query'][:60]}… » attendu {m['attendus']} / obtenu {m['top3']}")
    g = res["global"]
    print(f"[global] hit@1 {fmt(g['hit@1'], g['n'])} | hit@3 {fmt(g['hit@3'], g['n'])} | MRR {g['mrr']}")
    save("rag.json", res)


# --------------------------------------------------------------------------- moderator
def cmd_moderator(_args):
    from backend import config
    from backend.agents.agentmanager.agent import Agent
    from backend.agents.agentmanager.schemas import ModeratorResponse
    from backend.agents.agentmoderator.agent_moderator import Moderator

    system = Agent.read_file(config.PROMPT_PATH_MODERATOR / "moderator_system.txt")
    mod = Moderator()
    cases = json.loads((EVAL_DIR / "moderator_cases.json").read_text(encoding="utf-8"))["cases"]

    rows, errors = [], 0
    for c in cases:
        try:
            # call_and_validate direct : Moderator.moderate() masquerait une panne Groq en « injection ».
            out = mod.call_and_validate(
                messages=[{"role": "system", "content": system}, {"role": "user", "content": c["question"]}],
                model=config.MODEL_NAME_MODERATOR, temperature=0, schema=ModeratorResponse,
            )
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"erreur sur « {c['question'][:40]}… » : {exc}")
            continue
        rows.append({**c, "pred_injection": out.is_prompt_injection, "pred_off_topic": out.off_topic})

    legit = [r for r in rows if not r["is_prompt_injection"] and not r["off_topic"]]
    inj = [r for r in rows if r["is_prompt_injection"]]
    off = [r for r in rows if r["off_topic"] and not r["is_prompt_injection"]]
    fp = sum(r["pred_injection"] or r["pred_off_topic"] for r in legit)
    tp_inj = sum(r["pred_injection"] for r in inj)
    tp_off = sum(r["pred_off_topic"] for r in off)
    print(f"Faux positifs (questions légitimes bloquées) : {fmt(fp, len(legit))}")
    print(f"Injections détectées : {fmt(tp_inj, len(inj))}")
    print(f"Hors-sujet détectés : {fmt(tp_off, len(off))}")
    print(f"Erreurs d'appel (exclues) : {errors}")
    save("moderator.json", {"faux_positifs": [fp, len(legit)], "injections_detectees": [tp_inj, len(inj)],
                            "hors_sujet_detectes": [tp_off, len(off)], "erreurs": errors, "detail": rows})


# --------------------------------------------------------------------------- A/B
JUDGE_SYSTEM = (
    "Tu es un entraîneur expert chargé de comparer deux recommandations de coaching (A et B) pour la MÊME séquence "
    "de jeu, dans le sport indiqué (padel, tennis ou pickleball). Juge uniquement : (1) cohérence avec la séquence "
    "décrite, (2) caractère concret et réalisable de l'exercice, (3) spécificité au sport INDIQUÉ : un conseil qui "
    "relève d'un autre sport est un défaut. Ne tiens compte ni de la longueur ni de l'ordre. "
    'Réponds uniquement par un JSON : {"gagnant": "A"|"B"|"egalite", "raison": "une phrase"}.'
)


def _coach(sport, with_rag):
    import importlib

    folder, suffix, module, cls = SPORTS[sport]
    mod = importlib.import_module(f"backend.agents.{folder}.{module}")
    base = AGENTS / folder
    context = (base / f"context_{suffix}.txt").read_text(encoding="utf-8")
    prompt = (base / f"user_prompt_{suffix}.txt").read_text(encoding="utf-8")
    coach = getattr(mod, cls)(context, prompt)
    if not with_rag:
        class _NoRag:
            def retrieve(self, query, k=2):
                return []
        coach.knowledge_base = _NoRag()
    return coach, base


def _recommend(sport, with_rag, query, seq_id):
    coach, base = _coach(sport, with_rag)
    match = json.loads((base / "example_entry.json").read_text(encoding="utf-8"))
    match["donnees_sequences"] = [{
        "id_sequence": seq_id, "timestamp": "10:00", "evenement_cle": query,
        "metriques_video": {}, "contexte_tactique": "",
    }]
    return coach.generate_recommendations(match)


def _retry_json(fn, tries=3):
    """Réessaie si Groq renvoie 400 `json_validate_failed` (génération vide ou refusée, souvent ponctuelle).
    Les autres erreurs 400 (vrais bugs : mauvais modèle, requête invalide) remontent immédiatement."""
    import groq

    last = None
    for _ in range(tries):
        try:
            return fn()
        except groq.BadRequestError as exc:
            if "json_validate_failed" not in str(exc):
                raise
            last = exc
    raise last


def cmd_ab(args):
    from backend import config
    from backend.agents.agentmanager.agent import Agent
    from pydantic import BaseModel

    class Verdict(BaseModel):
        gagnant: str
        raison: str = ""

    rng = random.Random(args.seed)
    judge = Agent()
    items = [(s, it) for s, its in load_gold().items() for it in its]
    rng.shuffle(items)
    items = items[: args.n]

    rows, wins_rag, wins_base, ties = [], 0, 0, 0
    grounded = total_rec = 0
    echecs = []  # paires abandonnées après échecs répétés : déclarées dans le bilan, jamais ignorées en silence
    for i, (sport, it) in enumerate(items):
        try:
            with_r = _retry_json(lambda: _recommend(sport, True, it["query"], f"ab_{i}")).recommandations_coach[0]
            without = _retry_json(lambda: _recommend(sport, False, it["query"], f"ab_{i}")).recommandations_coach[0]

            rag_is_a = rng.random() < 0.5  # ordre aléatoire pour neutraliser le biais de position
            a, b = (with_r, without) if rag_is_a else (without, with_r)
            render = lambda r: f"Titre : {r.titre}\nConstat : {r.contenu.constat}\nAnalyse : {r.contenu.analyse}\nAction : {r.contenu.action_corrective}"  # noqa: E731
            v = _retry_json(lambda: judge.call_and_validate(
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": f"Sport : {sport}\nSéquence : {it['query']}\n\n=== A ===\n{render(a)}\n\n=== B ===\n{render(b)}"},
                ],
                model=config.MODEL_NAME_MODERATOR, temperature=0, schema=Verdict,
            ))
        except Exception as exc:  # noqa: BLE001
            echecs.append({"sport": sport, "query": it["query"], "erreur": str(exc)[:300]})
            print(f"[{i + 1}/{len(items)}] {sport:10s} → ABANDONNÉE ({type(exc).__name__})")
            continue

        total_rec += 1
        grounded += with_r.contenu.exercice_source_id in set(it["expected_ids"])
        g = v.gagnant.strip().upper()
        winner = "egalite" if g.startswith("E") else ("rag" if (g == "A") == rag_is_a else "sans_rag")
        wins_rag += winner == "rag"; wins_base += winner == "sans_rag"; ties += winner == "egalite"
        rows.append({"sport": sport, "query": it["query"], "gagnant": winner, "raison": v.raison,
                     "avec_rag": render(with_r), "sans_rag": render(without),
                     "exercice_cite": with_r.contenu.exercice_source_id, "attendus": it["expected_ids"]})
        print(f"[{i + 1}/{len(items)}] {sport:10s} → {winner}")

    decided = wins_rag + wins_base
    print(f"\nPaires évaluées : {len(rows)}/{len(items)} ({len(echecs)} abandonnée(s) après erreurs Groq répétées)")
    print(f"Avec RAG gagne : {fmt(wins_rag, decided)} des comparaisons tranchées ({ties} égalités)")
    print(f"Exercice attendu cité avec RAG : {fmt(grounded, total_rec)}")
    save("ab.json", {"avec_rag": wins_rag, "sans_rag": wins_base, "egalites": ties,
                     "exercice_attendu_cite": [grounded, total_rec], "paires_abandonnees": echecs, "detail": rows})

    # Fichier de notation en aveugle par un entraîneur humain (à remplir avant de dévoiler les colonnes de source).
    with open(RESULTS_DIR / "ab_notation_humaine.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "sport", "sequence", "reco_X", "reco_Y", "meilleure (X/Y/egalite)", "commentaire", "(source X)"])
        for i, r in enumerate(rows):
            flip = rng.random() < 0.5
            x, y = (r["avec_rag"], r["sans_rag"]) if flip else (r["sans_rag"], r["avec_rag"])
            w.writerow([i + 1, r["sport"], r["query"], x, y, "", "", "avec_rag" if flip else "sans_rag"])
    print("→ grille de notation humaine : ab_notation_humaine.csv dans le dossier des résultats (masquer la dernière colonne avant envoi)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("rag").set_defaults(fn=cmd_rag)
    sub.add_parser("moderator").set_defaults(fn=cmd_moderator)
    ab = sub.add_parser("ab")
    ab.add_argument("--n", type=int, default=12, help="nombre de séquences comparées (max 36)")
    ab.add_argument("--seed", type=int, default=42)
    ab.set_defaults(fn=cmd_ab)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()