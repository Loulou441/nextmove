"""Exceptions personnalisées pour la couche agents."""


class AgentError(Exception):
    """Erreur de base pour tous les agents NextMove."""


class EmptyResponseError(AgentError):
    """Le modèle a renvoyé une réponse vide."""


class InvalidResponseError(AgentError):
    """
    La réponse du modèle n'a pas pu être exploitée : JSON invalide ou
    ne respectant pas le schéma attendu, même après les tentatives de retry.
    """