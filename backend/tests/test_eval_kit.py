"""Tests hors-ligne du kit d'évaluation (scripts/eval/run_eval.py) : plomberie et calculs, pas qualité des agents."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.tests.test_agents_rag import VALID_REPLY, fake_embeddings, fake_groq  # noqa: F401  (fixtures)

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "eval" / "run_eval.py"


@pytest.fixture(scope="module")
def run_eval():
    spec = importlib.util.spec_from_file_location("run_eval", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gold_set_references_existing_drills(run_eval):
    for sport, items in run_eval.load_gold().items():
        ids = {d["id"] for d in json.loads(run_eval.kb_path(sport).read_text(encoding="utf-8"))}
        assert items, sport
        for it in items:
            assert it["expected_ids"] and set(it["expected_ids"]) <= ids, it["query"]


def test_moderator_cases_have_all_three_kinds(run_eval):
    cases = json.loads((SCRIPT.parent / "moderator_cases.json").read_text(encoding="utf-8"))["cases"]
    assert any(not c["is_prompt_injection"] and not c["off_topic"] for c in cases)
    assert any(c["is_prompt_injection"] for c in cases)
    assert any(c["off_topic"] and not c["is_prompt_injection"] for c in cases)


def test_wilson_interval_is_sane(run_eval):
    lo, hi = run_eval.wilson(30, 36)
    assert 0.6 < lo < 30 / 36 < hi < 0.95
    assert run_eval.wilson(0, 0) == (0.0, 0.0)
    assert run_eval.wilson(36, 36)[1] == pytest.approx(1.0)


def test_evaluate_rag_metrics_structure_and_bounds(run_eval, fake_embeddings):  # noqa: F811
    res = run_eval.evaluate_rag()

    assert set(res["par_sport"]) == {"padel", "tennis", "pickleball"}
    g = res["global"]
    assert g["n"] == 36
    assert 0 <= g["hit@1"] <= g["hit@3"] <= g["hit@5"] <= 36
    assert 0 < g["mrr"] <= 1


def test_evaluate_rag_counts_perfect_and_total_misses(run_eval):
    class PerfectKB:
        def __init__(self, items):
            self.items = {i["query"]: i["expected_ids"][0] for i in items}

        def retrieve(self, query, k=3):
            return [{"id": self.items[query]}] + [{"id": "autre"}] * (k - 1)

    class NullKB:
        def retrieve(self, query, k=3):
            return [{"id": "autre"}] * k

    gold = run_eval.load_gold()
    perfect = run_eval.evaluate_rag(get_kb=lambda s, p: PerfectKB(gold[s]))["global"]
    nothing = run_eval.evaluate_rag(get_kb=lambda s, p: NullKB())["global"]

    assert (perfect["hit@1"], perfect["mrr"]) == (36, 1.0)
    assert (nothing["hit@5"], nothing["mrr"]) == (0, 0.0)


def test_ab_comparison_unblinds_winner_correctly(run_eval, fake_embeddings, fake_groq, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(run_eval, "RESULTS_DIR", tmp_path)
    # 2 séquences x (coach avec RAG, coach sans RAG, juge). Le juge répond « A » à chaque fois :
    # le gagnant réel dépend donc de l'ordre tiré au hasard, que le script doit savoir démasquer.
    client = fake_groq([VALID_REPLY, VALID_REPLY, {"gagnant": "A", "raison": "x"}] * 2)

    run_eval.cmd_ab(SimpleNamespace(n=2, seed=0))

    out = json.loads((tmp_path / "ab.json").read_text(encoding="utf-8"))
    assert out["avec_rag"] + out["sans_rag"] + out["egalites"] == 2
    assert out["avec_rag"] + out["sans_rag"] == 2  # « A » n'est jamais une égalité
    assert len(client.calls) == 6
    # Le coach sans RAG ne reçoit aucun exercice de référence ; celui avec RAG en reçoit.
    with_rag, without_rag = client.calls[0]["messages"][1]["content"], client.calls[1]["messages"][1]["content"]
    assert '"exercices_references": []' in without_rag
    assert '"exercices_references": []' not in with_rag
    import csv

    with open(tmp_path / "ab_notation_humaine.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    assert len(rows) == 3 and rows[0][:2] == ["id", "sport"]
    assert {r[-1] for r in rows[1:]} <= {"avec_rag", "sans_rag"}


def test_ab_retries_then_skips_failed_pairs_and_reports_them(run_eval, fake_embeddings, fake_groq, monkeypatch, tmp_path):  # noqa: F811
    """Un 400 json_validate_failed est retenté ; si l'échec persiste, la paire est abandonnée ET comptée."""
    import httpx
    from groq import BadRequestError

    def bad_request():
        req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        body = {"error": {"code": "json_validate_failed", "message": "Failed to validate JSON"}}
        return BadRequestError("json_validate_failed", response=httpx.Response(400, request=req), body=body)

    monkeypatch.setattr(run_eval, "RESULTS_DIR", tmp_path)
    # Séquence 1 : le coach avec RAG échoue 1 fois puis réussit, tout le reste passe.
    # Séquence 2 : le coach avec RAG échoue 3 fois de suite -> paire abandonnée.
    fake_groq([
        bad_request(), VALID_REPLY, VALID_REPLY, {"gagnant": "A", "raison": "x"},
        bad_request(), bad_request(), bad_request(),
    ])

    run_eval.cmd_ab(SimpleNamespace(n=2, seed=0))

    out = json.loads((tmp_path / "ab.json").read_text(encoding="utf-8"))
    assert len(out["detail"]) == 1
    assert len(out["paires_abandonnees"]) == 1
    assert out["avec_rag"] + out["sans_rag"] == 1


def test_ab_judge_is_told_the_sport(run_eval, fake_embeddings, fake_groq, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(run_eval, "RESULTS_DIR", tmp_path)
    client = fake_groq([VALID_REPLY, VALID_REPLY, {"gagnant": "A", "raison": "x"}])

    run_eval.cmd_ab(SimpleNamespace(n=1, seed=0))

    judge_messages = client.calls[2]["messages"]
    assert "padel, tennis ou pickleball" in judge_messages[0]["content"]
    assert judge_messages[1]["content"].startswith("Sport : ")