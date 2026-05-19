from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import pandas as pd


@dataclass
class ResponsibilityResult:
    individual: int
    collective: int
    tactical: int
    explanation: str
    recommendations: List[str]
    confidence: str


def _clamp_100(a: int, b: int, c: int) -> Tuple[int, int, int]:
    total = a + b + c
    if total == 100:
        return a, b, c
    if total == 0:
        return 34, 33, 33
    a = round(a * 100 / total)
    b = round(b * 100 / total)
    c = 100 - a - b
    return a, b, c


def _zone_from_xy(x: float, y: float) -> str:
    if x >= 80:
        return "zone de finition (dernier tiers)"
    if x >= 55:
        return "milieu offensif (zone 14 et côtés)"
    if x >= 35:
        return "milieu de terrain"
    return "tiers défensif"


def analyze_key_event(event_row: Dict[str, Any], match_events: pd.DataFrame) -> ResponsibilityResult:
    """
    IA explicative v1 : règles simples + explications.
    event_row : dict d'une ligne sélectionnée
    match_events : tous les events du match (DataFrame)
    """

    event_type = str(event_row.get("type", "")).upper()
    phase = str(event_row.get("phase", "")).lower()
    x = float(event_row.get("x", 50))
    y = float(event_row.get("y", 50))
    minute = int(event_row.get("minute", 0))

    individual = 33
    collective = 34
    tactical = 33

    explanation_parts: List[str] = []
    recommendations: List[str] = []
    confidence = "Moyenne"

    zone = _zone_from_xy(x, y)

    if event_type == "GOAL":
        explanation_parts.append(f"But encaissé analysé autour de la {minute}e minute, dans la {zone}.")
        confidence = "Élevée"

        if phase == "transition":
            collective += 12
            tactical += 8
            individual -= 5
            explanation_parts.append("Le contexte indique une phase de transition, souvent liée à un déséquilibre après perte.")
            recommendations.append("Réduire les distances entre lignes lors des phases de perte de balle.")
            recommendations.append("Définir des règles de contre-pressing et de sécurisation (rest-defense).")

        if phase == "set-piece":
            tactical += 15
            collective += 5
            individual -= 5
            explanation_parts.append("Le but intervient sur phase arrêtée, la structure et l’organisation priment.")
            recommendations.append("Revoir l’organisation sur coups de pied arrêtés et les marquages (zone ou individuel).")

        if x >= 85:
            individual += 6
            explanation_parts.append("L’action se termine très près du but, ce qui peut traduire un duel perdu ou une intervention tardive.")
            recommendations.append("Travailler les duels défensifs proches de la surface et la temporisation.")

        recent_turnovers = match_events[
            (match_events["type"].str.upper() == "TURNOVER") &
            (match_events["minute"] >= minute - 5) &
            (match_events["minute"] <= minute)
        ]
        if len(recent_turnovers) >= 1:
            collective += 6
            explanation_parts.append("Une perte de balle récente est détectée avant le but, ce qui augmente le risque de transition.")
            recommendations.append("Améliorer la gestion du risque dans l’axe et les passes sous pression.")

    elif event_type == "TURNOVER":
        confidence = "Moyenne"
        explanation_parts.append(f"Perte de balle à la {minute}e minute dans la {zone}.")
        individual += 12
        collective += 6
        tactical -= 6

        if phase == "transition":
            collective += 6
            explanation_parts.append("La perte intervient dans une phase instable, l’équipe est potentiellement ouverte.")
            recommendations.append("Limiter les prises de risque dans l’axe en phase de transition.")
            recommendations.append("Mettre un soutien plus proche du porteur pour offrir une solution courte.")

        if x >= 55:
            collective += 4
            explanation_parts.append("La perte se situe en zone médiane ou offensive, ce qui expose les transitions adverses.")
            recommendations.append("Sécuriser la perte avec une couverture derrière le ballon (rest-defense).")

    elif event_type == "SHOT":
        confidence = "Faible"
        explanation_parts.append(f"Tir à la {minute}e minute dans la {zone}.")
        collective += 8
        tactical += 4
        individual -= 2

        if phase == "transition":
            collective += 6
            explanation_parts.append("Tir concédé en transition, signe de manque de contrôle après perte.")
            recommendations.append("Travailler les replis et la protection de l’axe sur transitions.")

        if x >= 80:
            individual += 4
            explanation_parts.append("Tir concédé près de la surface, possible retard dans le cadrage ou le pressing.")
            recommendations.append("Améliorer le cadrage porteur et le pressing de finition.")

    else:
        explanation_parts.append("Événement analysé, règles v1 appliquées.")
        confidence = "Faible"

    individual, collective, tactical = _clamp_100(individual, collective, tactical)

    explanation = " ".join(explanation_parts)
    if not recommendations:
        recommendations = ["Collecter plus de contexte ou annoter l’action pour améliorer l’explication."]

    return ResponsibilityResult(
        individual=individual,
        collective=collective,
        tactical=tactical,
        explanation=explanation,
        recommendations=recommendations,
        confidence=confidence
    )


def generate_tactical_narrative(result, event_row):
    """Génère un diagnostic textuel basé sur les scores de responsabilité."""
    
    # Analyse de la dominance
    if result.tactical > result.individual and result.tactical > result.collective:
        dominance = "une défaillance stratégique majeure. Le plan de jeu n'était pas adapté."
    elif result.collective > result.individual:
        dominance = "un manque de coordination collective. Le bloc était mal aligné."
    else:
        dominance = "une erreur d'exécution individuelle qui aurait pu être évitée."

    narrative = (
        f"**Diagnostic Tactique :** Cette action ({event_row['type']}) à la {event_row['minute']}e minute "
        f"révèle {dominance} \n\n"
        f"**Analyse de phase :** En phase de {event_row['phase']}, l'équipe a laissé trop d'espace "
        f"dans la zone x={event_row['x']}. "
    )
    
    return narrative