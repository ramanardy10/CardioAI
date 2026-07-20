"""Plotly figure builders for CardioAI. All charts pick up the active
palette so they read correctly in dark and light mode."""

import plotly.graph_objects as go

from ui.theme import palette, PLUM, ROSE, GOLD, GREEN


def _rgba(hex_color, alpha):
    """#RRGGBB + alpha -> 'rgba(r,g,b,a)'. Plotly rejects 8-digit hex in some
    trace properties (e.g. indicator gauge steps), so use this everywhere a
    translucent fill is needed inside a figure."""
    h = hex_color.lstrip("#")[:6]
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _base(fig, height=320):
    c = palette()
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["text"], family="Inter, sans-serif", size=13),
        xaxis=dict(gridcolor=c["border"], zerolinecolor=c["border"]),
        yaxis=dict(gridcolor=c["border"], zerolinecolor=c["border"]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def risk_gauge(prob, tuned, standard=0.5):
    band_color = GREEN if prob < tuned else (GOLD if prob < standard else ROSE)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob * 100,
        number={"suffix": "%", "font": {"size": 40}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": band_color, "thickness": 0.28},
            "steps": [
                {"range": [0, tuned * 100], "color": _rgba(GREEN, .2)},
                {"range": [tuned * 100, standard * 100], "color": _rgba(GOLD, .2)},
                {"range": [standard * 100, 100], "color": _rgba(ROSE, .2)},
            ],
            "threshold": {"line": {"color": ROSE, "width": 3},
                          "thickness": 0.75, "value": tuned * 100},
        },
    ))
    return _base(fig, 280)


def shap_waterfall(shap_df, top=8):
    d = shap_df.head(top).iloc[::-1]
    colors = [ROSE if v >= 0 else "#3B82C4" for v in d["shap"]]
    labels = [f"{r.label} = {r.value}" for r in d.itertuples()]
    fig = go.Figure(go.Bar(
        x=d["shap"], y=labels, orientation="h",
        marker_color=colors,
        text=[f"{v:+.3f}" for v in d["shap"]], textposition="outside",
    ))
    fig.add_vline(x=0, line_color=palette()["muted"], line_width=1)
    fig.update_layout(title="Per-patient SHAP contributions")
    return _base(fig, max(280, 42 * len(d)))


def timeline_chart(tl_df):
    c = palette()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tl_df["AgeCategory"], y=tl_df["risk"] * 100,
        mode="lines+markers", line=dict(color=ROSE, width=3, shape="spline"),
        marker=dict(size=7, color=ROSE), fill="tozeroy",
        fillcolor=_rgba(ROSE, .13), name="Modelled risk",
    ))
    cur = tl_df[tl_df["current"]]
    if len(cur):
        fig.add_trace(go.Scatter(
            x=cur["AgeCategory"], y=cur["risk"] * 100, mode="markers",
            marker=dict(size=16, color=PLUM, line=dict(color="#fff", width=2)),
            name="Current age",
        ))
    fig.update_layout(title="Risk across age groups (other factors held constant)",
                      yaxis_title="Risk (%)")
    fig.update_xaxes(tickangle=-40)
    return _base(fig, 360)


def distribution_hist(probs, tuned, standard=0.5):
    fig = go.Figure(go.Histogram(
        x=[p * 100 for p in probs], nbinsx=24, marker_color=PLUM,
        marker_line_color=ROSE, marker_line_width=.5, opacity=.85))
    fig.add_vline(x=tuned * 100, line_color=GOLD, line_dash="dash",
                  annotation_text="Tuned")
    fig.add_vline(x=standard * 100, line_color=ROSE, line_dash="dash",
                  annotation_text="0.50")
    fig.update_layout(title="Risk score distribution", xaxis_title="Risk (%)",
                      yaxis_title="Count")
    return _base(fig, 320)


def band_donut(counts):
    labels = list(counts.keys())
    fig = go.Figure(go.Pie(
        labels=labels, values=list(counts.values()), hole=.62,
        marker_colors=[{"Low": GREEN, "Elevated": GOLD, "High": ROSE}.get(k, PLUM)
                       for k in labels],
        textinfo="label+percent"))
    fig.update_layout(title="Risk band mix", showlegend=False)
    return _base(fig, 300)


def importance_bar(imp_df, top=12):
    d = imp_df.head(top).iloc[::-1]
    col = "importance" if "importance" in d.columns else d.columns[1]
    fig = go.Figure(go.Bar(
        x=d[col], y=d["label"], orientation="h",
        marker=dict(color=d[col], colorscale=[[0, PLUM], [1, ROSE]])))
    fig.update_layout(title="Global feature importance (SHAP)")
    return _base(fig, max(320, 30 * len(d)))
