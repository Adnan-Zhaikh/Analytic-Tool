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

def bar_chart(data, x, y, title="", orientation="v", text_auto=True):
    if data.empty:
        return _empty_figure("No data to display.")
    fig = px.bar(data, x=x, y=y, orientation=orientation, text_auto=text_auto)
    return _style(fig, title=title)

def histogram(data, column, title="", bins=40):
    if data.empty or column not in data.columns:
        return _empty_figure("No data to display.")
    fig = px.histogram(data, x=column, nbins=bins, marginal="box")
    return _style(fig, title=title)


def scatter_plot(data, x, y, title="", color=None, trendline=None):
    if data.empty:
        return _empty_figure("No data to display.")
    fig = px.scatter(data, x=x, y=y, color=color, trendline=trendline, opacity=0.7)
    return _style(fig, title=title)

def heatmap(corr, title="Correlation Matrix"):
    if corr is None or corr.empty:
        return _empty_figure("Need at least two numeric columns")

    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            colorscale="RdBu",
            zmid=0,                     # white at zero
            zmin=-1, zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            colorbar=dict(title="r"),
        )
    )
    return _style(fig, title, height=520)

def _empty_figure(message="No data"):
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#888"),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig
