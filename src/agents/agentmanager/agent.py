import sys
from pathlib import Path

if __name__ == "__main__":
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import GROQ_API_KEY
from groq import Groq
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class Agent:
	def __init__(self):
		self.client = Groq(api_key=GROQ_API_KEY)


	@staticmethod
	def read_file(file_path):
		with open(file_path, "r", encoding="utf-8") as file:
			return file.read()

	@staticmethod
	def afficher_rapport(data):
		"""Affiche le rapport de coaching dans la console (CLI) via rich."""
		# Titre principal
		console.print(Panel("[bold cyan] RAPPORT DE COACHING - NEXT MOVE[/bold cyan]", expand=False))

		for rec in data["recommandations_coach"]:
			# Création d'un tableau pour chaque action
			table = Table(title=f"\n[bold yellow]⏱ Séquence : {rec['timestamp']} - {rec['titre']}[/bold yellow]", show_header=True, header_style="bold magenta")

			table.add_column("Catégorie", style="dim", width=20)
			table.add_column("Analyse du Coach")

			c = rec["contenu"]
			table.add_row("📝 [bold]Constat[/bold]", c["constat"])
			table.add_row("🧠 [bold]Analyse[/bold]", c["analyse"])
			table.add_row("💡 [bold green]Action corrective[/bold green]", f"[green]{c['action_corrective']}[/green]")
			if c.get("pro_tip"):
				table.add_row("🌟 [bold blue]Pro-Tip[/bold blue]", f"[blue]{c['pro_tip']}[/blue]")

			console.print(table)