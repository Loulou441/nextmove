import plotly.graph_objects as go

def create_tactical_pitch(x, y, player_name, event_type, phase):
    fig = go.Figure()

    # Dessin du terrain (Herbe)
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="#228B22", line_color="white")
    
    # Lignes du terrain
    fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=100, line_color="white") # Médiane
    fig.add_shape(type="rect", x0=82, y0=20, x1=100, y1=80, line_color="white") # Surface de réparation
    
    # Ajout d'une "Heatmap" de danger autour du point de l'action
    fig.add_trace(go.Scatter(
        x=[x], y=[y],
        mode='markers',
        marker=dict(size=40, color='rgba(255, 0, 0, 0.3)', line=dict(width=0)),
        name="Zone d'impact"
    ))

    # Le point précis de l'action
    fig.add_trace(go.Scatter(
        x=[x], y=[y],
        mode='markers+text',
        marker=dict(size=12, color='white', line=dict(width=2, color='black')),
        text=[f"{player_name}"],
        textposition="top center",
        name=event_type
    ))

    fig.update_layout(
        title=f"Positionnement Tactique - Phase : {phase}",
        template="plotly_dark",
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 100], showgrid=False, zeroline=False, showticklabels=False),
        height=500,
        showlegend=False
    )
    return fig