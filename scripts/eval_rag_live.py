"""
Évaluation EN CONDITIONS RÉELLES des coachs et du RAG (à lancer en local).

Contrairement à backend/tests/test_agents_rag.py (hors-ligne, doubles de test),
ce script utilise le vrai modèle d'embedding (téléchargé depuis Hugging Face
au premier lancement) et, si GROQ_API_KEY est définie, le vrai LLM Groq.

Depuis la racine du dépôt, environnement installé :

    python scripts/eval_rag_live.py                 # RAG seul
    python scripts/eval_rag_live.py --llm           # + appel réel des 3 coachs
    python scripts/eval_rag_live.py --sport padel --llm

Vérifie :
  1. RAG : pour chaque exercice, une requête reformulée (probleme_associe sans
     le titre) retrouve-t-elle l'exercice dans le top-k ? (recall@1 / recall@3)
  2. RAG : les séquences de example_entry.json remontent-elles des exercices
     (affichage du top-3 pour relecture humaine) ?
  3. LLM (--llm) : réponse conforme au schéma, et exercice_source_id (s'il est
     renseigné) fait bien partie des exercices fournis par le RAG.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.agents.agentmanager.rag import enrich_match_data_with_drills, get_knowledge_base  # noqa: E402

SPORTS = {
    "padel": ("agentpadel", "padel", "agent_recommendation_padel", "PadelCoachAI"),
    "tennis": ("agenttennis", "tennis", "agent_recommendation_tennis", "TennisCoachAI"),
    "pickleball": ("agentpickelball", "pickelball", "agent_recommendation_pickelball", "PickelballCoachAI"),
}


def eval_retrieval(sport, folder, suffix):
    base = ROOT / "backend" / "agents" / folder
    kb_path = base / f"knowledge_{suffix}.json"
    drills = json.loads(kb_path.read_text(encoding="utf-8"))
    kb = get_knowledge_base(sport, kb_path)

    hit1 = hit3 = 0
    misses = []
    for d in drills:
        ids = [r["id"] for r in kb.retrieve(d["probleme_associe"], k=3)]
        hit1 += ids[:1] == [d["id"]]
        hit3 += d["id"] in ids
        if d["id"] not in ids:
            misses.append(d["id"])
    n = len(drills)
    print(f"[{sport}] recall@1 = {hit1}/{n} ({hit1 / n:.0%}) | recall@3 = {hit3}/{n} ({hit3 / n:.0%})")
    if misses:
        print(f"[{sport}] hors top-3 : {', '.join(misses)}")

    match_data = json.loads((base / "example_entry.json").read_text(encoding="utf-8"))
    enriched = enrich_match_data_with_drills(match_data, kb, k=3)
    for seq in enriched["donnees_sequences"]:
        print(f"  séquence « {seq['evenement_cle']} »")
        for r in seq["exercices_references"]:
            print(f"    {r['score_pertinence']:.2f}  {r['id']}  {r['titre']}")
    return kb


def eval_llm(sport, folder, suffix, module, cls):
    import importlib

    base = ROOT / "backend" / "agents" / folder
    mod = importlib.import_module(f"backend.agents.{folder}.{module}")
    context = (base / f"context_{suffix}.txt").read_text(encoding="utf-8")
    prompt = (base / f"user_prompt_{suffix}.txt").read_text(encoding="utf-8")
    match_data = json.loads((base / "example_entry.json").read_text(encoding="utf-8"))

    coach = getattr(mod, cls)(context, prompt)
    provided = {
        r["id"]
        for s in enrich_match_data_with_drills(match_data, coach.knowledge_base)["donnees_sequences"]
        for r in s["exercices_references"]
    }

    start = time.time()
    result = coach.generate_recommendations(match_data)
    elapsed = time.time() - start

    n_seq = len(match_data["donnees_sequences"])
    n_rec = len(result.recommandations_coach)
    cited = [r.contenu.exercice_source_id for r in result.recommandations_coach if r.contenu.exercice_source_id]
    invented = [c for c in cited if c not in provided]
    print(f"[{sport}] LLM ok en {elapsed:.1f}s | {n_rec} recommandation(s) pour {n_seq} séquence(s)")
    print(f"[{sport}] exercices cités : {cited or 'aucun'} | ids inventés (hors RAG) : {invented or 'aucun'}")
    return not invented


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", choices=SPORTS, help="un seul sport (défaut : tous)")
    parser.add_argument("--llm", action="store_true", help="appelle aussi Groq (nécessite GROQ_API_KEY)")
    args = parser.parse_args()

    ok = True
    for sport, (folder, suffix, module, cls) in SPORTS.items():
        if args.sport and sport != args.sport:
            continue
        eval_retrieval(sport, folder, suffix)
        if args.llm:
            ok &= eval_llm(sport, folder, suffix, module, cls)
        print()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()