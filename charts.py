import plotly.express as px
import plotly.graph_objects as go

TEMPLATES = "plotly_white"
PALETTE = px.colors.qualitative.Set2


def _style(fig, title="", height=420):
    """Apply consistent layout to any figure."""
    fig.update_layout(
        title=title,
        height=height,
        template=TEMPLATES,
        margin=dict(l=40, r=20, t=60, b=40),
        colorway=PALETTE,
        hovermode="x unified",
        font=dict(family="Arial", size=12),
    )
    return fig

def line_chart(data, x, y, title="", markers=True):
    if data.empty:
        return _empty_figure("No data to display.")
    fig = px.line(data, x=x, y=y, markers=markers)
    return _style(fig, title=title)

