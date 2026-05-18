from typing import Dict, Any
import pandas as pd


def compute_match_patterns(match_events: pd.DataFrame) -> Dict[str, Any]:

    summary = {}

    total_events = len(match_events)
    total_goals = (match_events["type"].str.upper() == "GOAL").sum()
    total_shots = (match_events["type"].str.upper() == "SHOT").sum()
    total_turnovers = (match_events["type"].str.upper() == "TURNOVER").sum()

    summary["total_events"] = int(total_events)
    summary["total_goals"] = int(total_goals)
    summary["total_shots"] = int(total_shots)
    summary["total_turnovers"] = int(total_turnovers)

    # Phases dangereuses
    phase_counts = match_events["phase"].value_counts().to_dict()
    summary["phase_distribution"] = phase_counts

    # Zones à risque (basées sur x)
    def zone(x):
        if x >= 80:
            return "Dernier tiers"
        elif x >= 55:
            return "Milieu offensif"
        elif x >= 35:
            return "Milieu"
        else:
            return "Tiers défensif"

    match_events["zone"] = match_events["x"].apply(zone)
    zone_counts = match_events["zone"].value_counts().to_dict()
    summary["zone_distribution"] = zone_counts

    # Détection simple vulnérabilité transition
    transition_events = match_events[
        match_events["phase"].str.lower() == "transition"
    ]

    summary["transition_risk_ratio"] = round(
        len(transition_events) / total_events, 2
    ) if total_events > 0 else 0

    # Génération synthèse automatique
    insights = []

    if summary["transition_risk_ratio"] > 0.4:
        insights.append("Forte exposition en phase de transition.")

    if summary["zone_distribution"].get("Dernier tiers", 0) > total_events * 0.3:
        insights.append("Volume élevé d'actions adverses dans le dernier tiers.")

    if total_turnovers > 2:
        insights.append("Nombre important de pertes de balle potentiellement dangereuses.")

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
