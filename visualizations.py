import plotly.graph_objects as go

def create_radar_chart(base_stats):
    """
    Creates an interactive radar chart (polar chart) for a given set of base stats.
    Expects base_stats to be a dictionary (e.g., {"hp": 45, "attack": 49, ...}).
    """
    categories = list(base_stats.keys())
    values = list(base_stats.values())
    
    # Close the radar chart loop by appending the first element.
    categories.append(categories[0])
    values.append(values[0])
    
    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Base Stats'
            )
        ]
    )
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, tickfont_size=10)
        ),
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False
    )
    
    return fig
