import sys
import json
import logging
from pathlib import Path
from typing import Optional, Type

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from groq import Groq, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError
from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config import GROQ_API_KEY
from src.agents.agentmanager.exceptions import EmptyResponseError, InvalidResponseError
from src.agents.agentmanager.schemas import RecommandationsCoach

console = Console()
logger = logging.getLogger("nextmove.agents")

# --- Paramètres de robustesse ---
# Nombre maximal de tentatives face à une erreur réseau/serveur Groq
GROQ_MAX_ATTEMPTS = 4
# Backoff exponentiel : 1s, 2s, 4s, 8s (plafonné) entre chaque tentative réseau
GROQ_RETRY_MIN_WAIT = 1
GROQ_RETRY_MAX_WAIT = 8

# Nombre maximal de tentatives face à une réponse mal formée (JSON invalide
# ou hors-schéma) — indépendant des erreurs réseau ci-dessus
MAX_VALIDATION_ATTEMPTS = 2

# Erreurs réseau/serveur transitoires pour lesquelles retenter l'appel a du sens.
# Volontairement exclu : les erreurs 4xx hors rate-limit (ex: BadRequestError) —
# ce sont des bugs de code ou de prompt, pas des incidents transitoires ;
# les retenter masquerait le problème au lieu de le faire remonter.
RETRYABLE_GROQ_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)


class Agent:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    @retry(
        retry=retry_if_exception_type(RETRYABLE_GROQ_ERRORS),
        stop=stop_after_attempt(GROQ_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=GROQ_RETRY_MIN_WAIT, max=GROQ_RETRY_MAX_WAIT),
        reraise=True,
    )
    def _call_groq(self, *, messages, model, temperature, response_format):
        """
        Appelle l'API Groq avec retry automatique (backoff exponentiel) sur
        les erreurs réseau, timeout, rate limit (429) et erreurs serveur (5xx).
        """
        return self.client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format=response_format,
        )

    def _parse_and_validate(self, raw_content: str, schema: Type[BaseModel]) -> BaseModel:
        """
        Transforme la chaîne JSON brute renvoyée par le modèle en instance
        Pydantic validée. Lève InvalidResponseError si le contenu n'est pas
        un JSON syntaxiquement valide, ou s'il ne respecte pas le schéma
        métier attendu (champ manquant, mauvais type...).
        """
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise InvalidResponseError(f"Réponse du modèle non-JSON : {exc}") from exc

        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise InvalidResponseError(f"Réponse du modèle hors-schéma : {exc}") from exc

    def call_and_validate(self, *, messages, model, temperature, schema: Type[BaseModel]) -> BaseModel:
        """
        Point d'entrée unique utilisé par tous les agents (modérateur et
        coachs sportifs) pour interroger Groq et obtenir une réponse
        structurée fiable.

        Combine deux niveaux de résilience :
          1. Retry réseau (_call_groq) sur les incidents transitoires Groq.
          2. Retry de contenu (boucle ci-dessous) si le modèle renvoie un
             JSON invalide ou incomplet malgré response_format="json_object" :
             ce format garantit un JSON syntaxiquement valide, jamais qu'il
             respecte le schéma métier attendu (response_format ne connaît
             pas nos champs "constat"/"analyse"/etc.).

        Lève EmptyResponseError ou InvalidResponseError si, après toutes les
        tentatives, aucune réponse exploitable n'a pu être obtenue — à
        l'appelant de décider de la conduite à tenir.
        """
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
            response = self._call_groq(
                messages=messages,
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
            )

            raw_content = response.choices[0].message.content
            if raw_content is None:
                last_error = EmptyResponseError("Le modèle a renvoyé une réponse vide.")
                logger.warning("Réponse vide du modèle (tentative %s/%s).", attempt, MAX_VALIDATION_ATTEMPTS)
                continue

            try:
                return self._parse_and_validate(raw_content, schema)
            except InvalidResponseError as exc:
                last_error = exc
                logger.warning(
                    "Réponse invalide du modèle (tentative %s/%s) : %s",
                    attempt, MAX_VALIDATION_ATTEMPTS, exc,
                )

        raise last_error

    @staticmethod
    def afficher_rapport(data: RecommandationsCoach):
        """Affiche le rapport de coaching dans la console (CLI) via rich."""
        console.print(Panel("[bold cyan] RAPPORT DE COACHING - NEXT MOVE[/bold cyan]", expand=False))

        for rec in data.recommandations_coach:
            table = Table(
                title=f"\n[bold yellow]⏱ Séquence : {rec.timestamp} - {rec.titre}[/bold yellow]",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Catégorie", style="dim", width=20)
            table.add_column("Analyse du Coach")

            table.add_row("📝 [bold]Constat[/bold]", rec.contenu.constat)
            table.add_row("🧠 [bold]Analyse[/bold]", rec.contenu.analyse)
            table.add_row(
                "💡 [bold green]Action corrective[/bold green]",
                f"[green]{rec.contenu.action_corrective}[/green]",
            )
            if rec.contenu.pro_tip:
                table.add_row("🌟 [bold blue]Pro-Tip[/bold blue]", f"[blue]{rec.contenu.pro_tip}[/blue]")
            if rec.contenu.exercice_source_id:
                table.add_row(
                    "🔗 [bold cyan]Exercice de référence[/bold cyan]",
                    f"[cyan]{rec.contenu.exercice_source_id}[/cyan]",
                )

            console.print(table)