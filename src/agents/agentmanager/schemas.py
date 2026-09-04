"""
Schémas Pydantic partagés pour valider les réponses des agents Groq.

Ces modèles servent de contrat de données entre les prompts systèmes
(qui définissent le format JSON attendu en langage naturel) et le code
applicatif, qui a besoin d'une garantie structurelle sur les champs
reçus avant de les utiliser.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ContenuRecommandation(BaseModel):
    """Contenu détaillé d'une recommandation de coaching pour une séquence."""

    constat: str = Field(..., min_length=1, description="Ce qui s'est passé durant la séquence.")
    analyse: str = Field(..., min_length=1, description="Pourquoi cela s'est produit.")
    action_corrective: str = Field(..., min_length=1, description="Exercice ou conseil concret.")
    pro_tip: Optional[str] = Field(default=None, description="Référence à un joueur professionnel, si pertinente.")


class Recommandation(BaseModel):
    """Une recommandation de coaching pour une séquence identifiée du match."""

    timestamp: str = Field(..., min_length=1)
    titre: str = Field(..., min_length=1)
    contenu: ContenuRecommandation


class RecommandationsCoach(BaseModel):
    """Schéma complet attendu en sortie des agents coachs sportifs."""

    recommandations_coach: List[Recommandation] = Field(..., min_length=1)


class ModeratorResponse(BaseModel):
    """Schéma attendu en sortie de l'agent modérateur."""

    is_prompt_injection: bool