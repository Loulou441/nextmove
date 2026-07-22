from typing import Dict, Any
import pandas as pd


def compute_match_patterns(match_events: pd.DataFrame) -> Dict[str, Any]:
    """Analyse des patterns tactiques d'un match de pickleball."""

    summary = {}

    total_events = len(match_events)
    total_winners = (match_events["type"].str.upper() == "WINNER").sum()
    total_shots = (match_events["type"].str.upper() == "SHOT").sum()
    total_errors = (match_events["type"].str.upper() == "ERROR").sum()

    summary["total_events"] = int(total_events)
    summary["total_winners"] = int(total_winners)
    summary["total_shots"] = int(total_shots)
    summary["total_errors"] = int(total_errors)

    # Phases de jeu dangereuses (service, transition, filet/kitchen)
    phase_counts = match_events["phase"].value_counts().to_dict()
    summary["phase_distribution"] = phase_counts

    # Zones à risque (basées sur la distance au filet, x=100 -> au filet)
    def zone(x):
        if x >= 80:
            return "Zone du filet (Kitchen)"
        elif x >= 55:
            return "Zone de transition avant"
        elif x >= 35:
            return "Zone médiane"
        else:
            return "Zone de fond de court (service)"

    match_events["zone"] = match_events["x"].apply(zone)
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

    if summary["zone_distribution"].get("Zone du filet (Kitchen)", 0) > total_events * 0.3:
        insights.append("Volume élevé d'échanges dans la zone du filet (Kitchen).")

    if total_errors > 2:
        insights.append("Nombre important d'erreurs non forcées potentiellement évitables.")

    if not insights:
        insights.append("Pas de vulnérabilité structurelle majeure détectée sur ce match (selon règles POC).")

    summary["insights"] = insights

    # Priorité d'action simple
    if summary["transition_risk_ratio"] > 0.5:
        summary["priority_level"] = "Élevée"
    elif summary["transition_risk_ratio"] > 0.3:
        summary["priority_level"] = "Moyenne"
    else:
        summary["priority_level"] = "Faible"

    return summary

