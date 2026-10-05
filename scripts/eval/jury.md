# Évaluer les coachs NextMove — guide pour le jury

## Ce qu'on peut affirmer (et avec quelle preuve)

| Affirmation | Preuve | Commande |
|---|---|---|
| Le RAG retrouve les bons exercices | hit@1 / hit@3 / MRR sur 36 requêtes annotées, avec intervalle de confiance | `python scripts/eval/run_eval.py rag` |
| Le RAG améliore les recommandations | Comparaison en aveugle avec/sans RAG (juge LLM + notation humaine d'un échantillon) | `python scripts/eval/run_eval.py ab --n 36` |
| Le coach ne s'appuie que sur des exercices réels | Taux d'exercices attendus cités, aucun id inventé | `ab` et `scripts/eval_rag_live.py --llm` |
| Le modérateur protège sans gêner | Détection des injections / hors-sujet, taux de faux positifs | `python scripts/eval/run_eval.py moderator` |
| Le code est robuste | 186 tests automatisés (retries, validation, repli du modérateur) | `pytest backend/tests` |

## Ce qu'on ne peut PAS affirmer avec ce kit

- **« Les joueurs progressent grâce au coach. »** Cela demande une étude avec de vrais joueurs
  (avant/après, groupe témoin). Présentez-le comme une perspective.
- **« Les conseils sont bons »** sur la seule base du juge LLM : il peut préférer ses propres
  formulations. Faites noter un échantillon (20–30 cas) par un entraîneur avec
  `results/ab_notation_humaine.csv` (colonnes X/Y en aveugle) et citez cette note en priorité.
- **Les chiffres du RAG comme une vérité générale** : le jeu de 36 requêtes est un brouillon écrit
  par un assistant, à faire relire par un entraîneur ; avec n = 12 par sport, les intervalles de
  confiance sont larges (affichés par le script).

## Protocole conseillé (≈ 1 h)

1. Faire relire `gold_rag.json` par un entraîneur (corriger/ajouter des `expected_ids`).
2. `check`, puis `rag`, puis `moderator`, puis `ab --n 36`.
3. Faire noter `ab_notation_humaine.csv` par l'entraîneur (sans la colonne source), puis comparer
   avec le verdict du juge LLM (accord = signal de fiabilité).
4. Présenter les chiffres **avec** les intervalles de confiance et les limites ci-dessus : un
   résultat honnête, même modeste, est plus crédible qu'un 100 % sans protocole.