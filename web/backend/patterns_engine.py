from typing import Dict, Any
import pandas as pd

# Libellés de zone par sport (distance normalisée au filet, x=100 -> au filet),
# cohérents avec les zones utilisées par src/services/cv_pipeline.py.
_ZONE_LABELS = {
    "pickleball": [
        (80, "Zone du filet (Kitchen)"),
        (55, "Zone de transition avant"),
        (35, "Zone médiane"),
        (0, "Zone de fond de court (service)"),
    ],
    "padel": [
        (80, "Zone du filet"),
        (55, "Zone médiane"),
        (30, "Zone de fond de court"),
        (0, "Couloirs latéraux"),
    ],
    "tennis": [
        (80, "Zone du filet"),
        (55, "Zone médiane"),
        (30, "Zone de fond de court"),
        (0, "Couloirs"),
    ],
}


def compute_match_patterns(match_events: pd.DataFrame, sport: str = "pickleball") -> Dict[str, Any]:
    """
    Analyse des patterns tactiques d'un match à partir de ses événements
    (`match_events` : une ligne par événement détecté, colonnes attendues
    "event_type" — SHOT/WINNER/ERROR —, "phase" et "x").
    """
    summary = {}

    total_events = len(match_events)
    total_winners = (match_events["event_type"].str.upper() == "WINNER").sum()
    total_shots = (match_events["event_type"].str.upper() == "SHOT").sum()
    total_errors = (match_events["event_type"].str.upper() == "ERROR").sum()

    summary["total_events"] = int(total_events)
    summary["total_winners"] = int(total_winners)
    summary["total_shots"] = int(total_shots)
    summary["total_errors"] = int(total_errors)

    # Phases de jeu dangereuses (service, transition, filet/kitchen)
    phase_counts = match_events["phase"].value_counts().to_dict()
    summary["phase_distribution"] = phase_counts

    # Zones à risque (basées sur la distance au filet, x=100 -> au filet)
    zone_bounds = _ZONE_LABELS.get(sport, _ZONE_LABELS["pickleball"])

    def zone(x):
        for threshold, label in zone_bounds:
            if x >= threshold:
                return label
        return zone_bounds[-1][1]

    match_events = match_events.assign(zone=match_events["x"].apply(zone))
    zone_counts = match_events["zone"].value_counts().to_dict()
    summary["zone_distribution"] = zone_counts

    # Détection simple de vulnérabilité en phase de transition
    transition_events = match_events[
        match_events["phase"].str.lower() == "transition"
    ]

    summary["transition_risk_ratio"] = round(
        len(transition_events) / total_events, 2
    ) if total_events > 0 else 0

    # Génération synthèse automatique
    insights = []

    if summary["transition_risk_ratio"] > 0.4:
        insights.append("Forte exposition en phase de transition avant le filet.")

    if zone_counts:
        top_zone = max(zone_counts, key=zone_counts.get)
        if zone_counts[top_zone] > total_events * 0.3:
            insights.append(f"Volume élevé d'échanges dans la zone : {top_zone}.")

    if total_errors > total_winners:
        insights.append("Nombre important d'erreurs non forcées potentiellement évitables.")

    if not insights:
        insights.append("Bon contrôle global, peu d'erreurs non forcées.")

    summary["insights"] = insights

    # Priorité d'action simple
    if summary["transition_risk_ratio"] > 0.5:
        summary["priority_level"] = "Élevée"
    elif summary["transition_risk_ratio"] > 0.3:
        summary["priority_level"] = "Moyenne"
    else:
        summary["priority_level"] = "Faible"

    return summary
