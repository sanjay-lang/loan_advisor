from pathlib import Path

import plotly.graph_objects as go


BASE_DIR = Path(__file__).resolve().parent


def create_savings_chart(monthly_saving, transfer_cost, net_savings):
    labels = ["Monthly Saving", "Transfer Cost", "Net Saving"]
    values = [monthly_saving, transfer_cost, net_savings]
    colors = ["#2563eb", "#f59e0b", "#16a34a"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=colors,
                text=[f"₹{value:,.0f}" for value in values],
                textposition="outside",
                cliponaxis=False
            )
        ]
    )

    fig.update_layout(
        title="Balance Transfer Savings Overview",
        xaxis_title="Amount in rupees (log scale)",
        xaxis_type="log",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=120, r=110, t=70, b=60),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial")
    )

    fig.write_html(BASE_DIR / "savings_chart.html", include_plotlyjs=True)


def create_break_even_chart(timeline):
    months = [point["month"] for point in timeline]
    positions = [point["position"] for point in timeline]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=months,
                y=positions,
                mode="lines+markers",
                line=dict(color="#243c8f", width=4),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor="rgba(36, 60, 143, 0.10)",
                hovertemplate="Month %{x}<br>Net position: ₹%{y:,.0f}<extra></extra>",
            )
        ]
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#16a34a")
    fig.update_layout(
        title="Break-even Timeline",
        xaxis_title="Month",
        yaxis_title="Cumulative net position",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial"),
        margin=dict(l=80, r=30, t=70, b=60),
    )
    fig.write_html(BASE_DIR / "break_even_chart.html", include_plotlyjs=True)
