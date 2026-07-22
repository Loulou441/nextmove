from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def afficher_rapport(data):
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
