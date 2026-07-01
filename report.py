from pathlib import Path
import math

import plotly.graph_objects as go


BASE_DIR = Path(__file__).resolve().parent


def format_axis_rupees(value):
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 100000:
        return f"{sign}₹{value / 100000:.0f}L"
    if value >= 1000:
        return f"{sign}₹{value / 1000:.0f}K"
    return f"{sign}₹{value:.0f}"


def get_nice_tick_step(raw_step):
    candidates = [
        1000,
        2000,
        5000,
        10000,
        20000,
        50000,
        100000,
        200000,
        500000,
        1000000,
        2000000,
        5000000,
    ]
    return min(candidates, key=lambda step: abs(math.log(step / raw_step)))


def create_savings_chart(monthly_saving, transfer_cost, net_savings):
    labels = ["Monthly Saving", "Transfer Cost", "Net Saving"]
    values = [monthly_saving, transfer_cost, net_savings]
    colors = ["#2563eb", "#f59e0b", "#16a34a"]
    min_value = min(values + [0])
    max_value = max(values + [0])
    tick_step = get_nice_tick_step(max((max_value - min_value) / 5, 1000))
    axis_min = math.floor(min_value * 1.12 / tick_step) * tick_step
    axis_max = math.ceil(max_value * 1.12 / tick_step) * tick_step
    tick_values = list(range(int(axis_min), int(axis_max + tick_step), int(tick_step)))

    fig = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=colors,
                text=[f"₹{value:,.0f}" for value in values],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{y}: ₹%{x:,.0f}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="Balance Transfer Savings Overview",
        xaxis_title="Amount in rupees",
        yaxis_title="",
        showlegend=False,
        bargap=0.28,
        height=420,
        margin=dict(l=150, r=130, t=80, b=80),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", color="#24364f"),
        title_font=dict(size=22, color="#24364f"),
    )
    fig.update_xaxes(
        range=[axis_min, axis_max],
        tickmode="array",
        tickvals=tick_values,
        ticktext=[format_axis_rupees(value) for value in tick_values],
        showgrid=True,
        gridcolor="#e8eef6",
        zeroline=True,
        zerolinecolor="#cbd5e1",
        linecolor="#dbe3ef",
    )
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=labels,
        ticks="",
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
