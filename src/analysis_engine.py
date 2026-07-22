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
        return "zone du filet (Kitchen)"
    if x >= 55:
        return "zone de transition avant"
    if x >= 35:
        return "zone médiane"
    return "fond de court (service)"


def analyze_key_event(event_row: Dict[str, Any], match_events: pd.DataFrame) -> ResponsibilityResult:
    """
    IA explicative v1 : règles simples + explications (pickleball).
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

    if event_type == "WINNER":
        explanation_parts.append(f"Point gagné analysé autour de la {minute}e minute, dans la {zone}.")
        confidence = "Élevée"

        if phase == "transition":
            collective += 12
            tactical += 8
            individual -= 5
            explanation_parts.append("Le contexte indique une phase de transition vers le filet, souvent liée à une prise d'initiative bien préparée.")
            recommendations.append("Reproduire ce schéma de montée au filet en binôme lors des prochains points.")
            recommendations.append("Continuer à synchroniser les déplacements avec le partenaire lors de la transition.")

        if phase == "service":
            tactical += 15
            collective += 5
            individual -= 5
            explanation_parts.append("Le point intervient sur le service, la structure et le placement de retour priment.")
            recommendations.append("Revoir le placement de service et la stratégie de retour pour reproduire ce point.")

        if x >= 85:
            individual += 6
            explanation_parts.append("L'action se termine très près du filet, ce qui traduit une bonne prise de temps en Kitchen.")
            recommendations.append("Continuer à travailler la patience dans les échanges de dinks avant l'attaque.")

        recent_errors = match_events[
            (match_events["type"].str.upper() == "ERROR") &
            (match_events["minute"] >= minute - 5) &
            (match_events["minute"] <= minute)
        ]
        if len(recent_errors) >= 1:
            collective += 6
            explanation_parts.append("Une erreur non forcée récente est détectée avant ce point, ce qui augmente le risque d'instabilité.")
            recommendations.append("Améliorer la gestion du risque et la constance dans les échanges sous pression.")

    elif event_type == "ERROR":
        confidence = "Moyenne"
        explanation_parts.append(f"Erreur non forcée à la {minute}e minute dans la {zone}.")
        individual += 12
        collective += 6
        tactical -= 6

        if phase == "transition":
            collective += 6
            explanation_parts.append("L'erreur intervient dans une phase instable, le binôme est potentiellement mal synchronisé.")
            recommendations.append("Limiter les prises de risque pendant la transition vers le filet.")
            recommendations.append("Mettre en place un signal clair avec le partenaire pour la montée au filet.")

        if x >= 55:
            collective += 4
            explanation_parts.append("L'erreur se situe en zone avancée, ce qui expose le point suivant à l'adversaire.")
            recommendations.append("Sécuriser l'échange avec un coup plus prudent avant de tenter l'attaque.")

    elif event_type == "SHOT":
        confidence = "Faible"
        explanation_parts.append(f"Coup joué à la {minute}e minute dans la {zone}.")
        collective += 8
        tactical += 4
        individual -= 2

        if phase == "transition":
            collective += 6
            explanation_parts.append("Coup joué en transition, signe d'une prise d'initiative avant la stabilisation au filet.")
            recommendations.append("Travailler le timing de la montée au filet après le service ou le retour.")

        if x >= 80:
            individual += 4
            explanation_parts.append("Coup joué près du filet, possible retard dans la préparation du dink ou du volley.")
            recommendations.append("Améliorer la préparation de la raquette avant les échanges au filet.")

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
        dominance = "un manque de coordination avec le partenaire. Le binôme était mal synchronisé."
    else:
        dominance = "une erreur d'exécution individuelle qui aurait pu être évitée."

    narrative = (
        f"**Diagnostic Tactique :** Cette action ({event_row['type']}) à la {event_row['minute']}e minute "
        f"révèle {dominance} \n\n"
        f"**Analyse de phase :** En phase de {event_row['phase']}, le joueur a laissé trop d'espace "
        f"dans la zone x={event_row['x']}. "
    )
    
    return narrative