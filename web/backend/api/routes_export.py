"""
Export PDF d'un match — génère un document structuré côté serveur via un
vrai navigateur headless (Playwright/Chromium), ce qui permet d'utiliser du
CSS moderne (Flexbox, couleurs, coins arrondis) sans les limitations d'un
convertisseur HTML->PDF classique comme xhtml2pdf.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from playwright.sync_api import sync_playwright

from api.deps import get_db, get_current_user
from db.models import User, Match

router = APIRouter(prefix="/matches", tags=["export"])


def _render_html(match: Match) -> str:
    """Construit le document HTML/CSS — rendu par un vrai Chromium, donc
    tout le CSS moderne (Flexbox, border-radius, dégradés) est disponible."""
    skills_html = ""
    for skill in (match.skills or []):
        score = skill.get("score", 0)
        pct = int((score / 5) * 100)
        skills_html += f"""
        <div class="skill-row">
            <div class="skill-top">
                <span class="skill-label">{skill.get('icon', '')} {skill.get('label', '')}</span>
                <span class="skill-score">{score}</span>
            </div>
            <div class="bar-bg"><div class="bar-fill green" style="width:{pct}%;"></div></div>
        </div>
        """

    highlights_html = ""
    for h in (match.highlights or []):
        highlights_html += f"""
        <div class="highlight-row">
            <div>
                <div class="hl-title">{h.get('title', '')}</div>
                <div class="hl-time">{h.get('time', '')}</div>
            </div>
            <span class="tag">{h.get('tag', '')}</span>
        </div>
        """

    insights_html = "".join(f"<li>{i.get('text', '')}</li>" for i in (match.insights or []))

    patterns = match.patterns_summary or {}
    pattern_insights_html = "".join(f"<li>{text}</li>" for text in patterns.get("insights", []))
    priority = patterns.get("priority_level", "")
    priority_class = "orange" if priority == "Élevée" else "green"

    def distribution_block(title, data: dict):
        if not data:
            return ""
        total = sum(data.values()) or 1
        rows = ""
        for label, count in data.items():
            pct = int((count / total) * 100)
            rows += f"""
            <div class="dist-row">
                <div class="dist-top"><span>{label}</span><span class="dist-pct">{pct}%</span></div>
                <div class="bar-bg small"><div class="bar-fill blue" style="width:{pct}%;"></div></div>
            </div>
            """
        return f"<p class='block-title'>{title}</p>{rows}"

    phase_html = distribution_block("Répartition par phase de jeu", patterns.get("phase_distribution", {}))
    zone_html = distribution_block("Répartition par zone du terrain", patterns.get("zone_distribution", {}))

    generated_at = datetime.now().strftime("%d/%m/%Y à %H:%M")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
            color: #1C1C1E;
            background: #F2F2F7;
            margin: 0;
            padding: 24px;
            font-size: 13px;
        }}
        .brand {{
            display: flex; align-items: center; gap: 8px;
            margin-bottom: 14px; font-size: 13px; font-weight: bold; color: #1C1C1E;
        }}
        .brand-emoji {{ font-size: 18px; }}

        .header {{
            background: linear-gradient(135deg, #34C759, #28B84C);
            color: white;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 16px;
        }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 6px 0 0 0; opacity: 0.9; }}

        .card {{
            background: white;
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }}
        .card h2 {{ font-size: 15px; margin: 0 0 12px 0; }}

        .kpi-grid {{ display: flex; gap: 10px; }}
        .kpi {{ flex: 1; background: #F2F2F7; border-radius: 12px; text-align: center; padding: 12px 0; }}
        .kpi-value {{ font-size: 20px; font-weight: bold; }}
        .kpi-label {{ font-size: 10px; color: #8E8E93; }}

        .bar-bg {{ background: #E5E5EA; height: 8px; border-radius: 4px; overflow: hidden; }}
        .bar-bg.small {{ height: 6px; }}
        .bar-fill {{ height: 100%; border-radius: 4px; }}
        .bar-fill.green {{ background: #34C759; }}
        .bar-fill.blue {{ background: #007AFF; }}

        .skill-row {{ margin-bottom: 10px; }}
        .skill-top {{ display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px; }}
        .skill-score {{ color: #34C759; font-weight: bold; }}

        .highlight-row {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 8px 0; border-bottom: 1px solid #F2F2F7;
        }}
        .highlight-row:last-child {{ border-bottom: none; }}
        .hl-title {{ font-size: 12px; font-weight: 500; }}
        .hl-time {{ font-size: 10px; color: #8E8E93; }}
        .tag {{ background: #D1F0DC; color: #1A7F3C; font-size: 9px; font-weight: bold;
                padding: 3px 10px; border-radius: 10px; }}

        .priority-badge {{
            display: inline-block; padding: 4px 12px; border-radius: 10px;
            font-size: 10px; font-weight: bold; margin-left: 8px;
        }}
        .priority-badge.orange {{ background: #FFE4CC; color: #B35500; }}
        .priority-badge.green {{ background: #D1F0DC; color: #1A7F3C; }}

        .block-title {{ font-size: 10px; color: #8E8E93; text-transform: uppercase; margin: 14px 0 8px 0; }}
        .dist-row {{ margin-bottom: 8px; }}
        .dist-top {{ display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 3px; }}

        ul {{ font-size: 12px; padding-left: 18px; margin: 6px 0; }}
        li {{ margin-bottom: 5px; }}

        .footer {{
            text-align: center; font-size: 9px; color: #8E8E93; margin-top: 20px;
        }}
    </style>
    </head>
    <body>
        <div class="brand"><span class="brand-emoji">🏓</span> NextMove</div>

        <div class="header">
            <h1>{match.title}</h1>
            <p>{match.sport.capitalize()} — {match.match_date.strftime('%d/%m/%Y') if match.match_date else ''}</p>
        </div>

        <div class="card">
            <div class="kpi-grid">
                <div class="kpi"><div class="kpi-value">{match.rating or '-'}</div><div class="kpi-label">NOTE</div></div>
                <div class="kpi"><div class="kpi-value">{match.rallies or '-'}</div><div class="kpi-label">RALLIES</div></div>
                <div class="kpi"><div class="kpi-value">{match.winners or '-'}</div><div class="kpi-label">WINNERS</div></div>
                <div class="kpi"><div class="kpi-value">{match.errors or '-'}</div><div class="kpi-label">ERREURS</div></div>
            </div>
        </div>

        <div class="card">
            <h2>Couverture de terrain</h2>
            <div class="bar-bg"><div class="bar-fill green" style="width:{match.coverage or 0}%;"></div></div>
        </div>

        <div class="card">
            <h2>Compétences</h2>
            {skills_html}
        </div>

        <div class="card">
            <h2>Temps forts</h2>
            {highlights_html}
        </div>

        <div class="card">
            <h2>Analyse tactique <span class="priority-badge {priority_class}">Priorité {priority}</span></h2>
            <ul>{pattern_insights_html}</ul>
            {phase_html}
            {zone_html}
        </div>

        <div class="card">
            <h2>Analyse générale</h2>
            <ul>{insights_html}</ul>
        </div>

        <div class="footer">Généré par NextMove le {generated_at}</div>
    </body>
    </html>
    """


@router.get("/{match_id}/export-pdf")
def export_match_pdf(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Génère et renvoie un PDF du dashboard de ce match, rendu par Chromium."""
    match = (
        db.query(Match)
        .filter(Match.id == match_id, Match.user_id == current_user.id)
        .first()
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match introuvable")

    html = _render_html(match)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()

    safe_title = match.title.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'},
    )