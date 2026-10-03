"""Visual components and Plotly chart renderers for the Board Man Gets Paid dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BRACKET_COLORS = {
    0: "#10B981",  # Sub-tax: Green
    1: "#F59E0B",  # Tax to 1st Apron: Amber
    2: "#F97316",  # 1st to 2nd Apron: Orange
    3: "#EF4444",  # Above 2nd Apron: Red
}

BRACKET_NAMES = {
    0: "Bracket 0 (< Tax, λ=0.00)",
    1: "Bracket 1 (Tax, λ=0.15)",
    2: "Bracket 2 (1st Apron, λ=0.35)",
    3: "Bracket 3 (2nd Apron, λ=0.70)",
}


def render_surplus_scatter(df_board: pd.DataFrame) -> go.Figure:
    """Build an interactive scatter plot of Cap Hit vs Fair Production Value."""
    df_plot = df_board[df_board["salary"] > 0].copy()
    df_plot["salary_m"] = df_plot["salary"] / 1_000_000.0
    df_plot["fair_value_m"] = df_plot["fair_value"] / 1_000_000.0
    df_plot["net_surplus_m"] = df_plot["net_surplus"] / 1_000_000.0
    df_plot["friction_m"] = df_plot["friction_tax"] / 1_000_000.0
    df_plot["bracket_label"] = df_plot["bracket"].map(BRACKET_NAMES)

    fig = go.Figure()

    # Add diagonal fair value line (y = x)
    max_val = max(df_plot["salary_m"].max(), df_plot["fair_value_m"].max()) + 5.0
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode="lines",
            line=dict(color="rgba(156, 163, 175, 0.4)", dash="dash", width=1.5),
            name="Fair Value Baseline (FV = Cap Hit)",
            hoverinfo="skip",
        )
    )

    # Add points per bracket
    for b in sorted(df_plot["bracket"].unique()):
        subset = df_plot[df_plot["bracket"] == b]
        fig.add_trace(
            go.Scatter(
                x=subset["salary_m"],
                y=subset["fair_value_m"],
                mode="markers",
                name=BRACKET_NAMES.get(b, f"Bracket {b}"),
                marker=dict(
                    color=BRACKET_COLORS.get(b, "#6B7280"),
                    size=9,
                    opacity=0.85,
                    line=dict(width=1, color="#1F2937"),
                ),
                customdata=subset[
                    ["player_name", "team", "war", "net_surplus_m", "friction_m", "surplus_efficiency"]
                ],
                hovertemplate=(
                    "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                    "Cap Hit: $%{x:.1f}M<br>"
                    "Fair Production Value: $%{y:.1f}M<br>"
                    "WAR (VORP): %{customdata[2]:.1f}<br>"
                    "Apron Friction: -$%{customdata[4]:.2f}M<br>"
                    "<b>Net Surplus (NSV): $%{customdata[3]:+.1f}M</b><br>"
                    "Efficiency (NSV/$): %{customdata[5]:.2f}x<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=dict(
            text="<b>NBA Contract Efficiency & Apron Drag (2025-26)</b>",
            font=dict(size=18),
        ),
        xaxis=dict(title="Annual Cap Hit ($ Millions)", gridcolor="rgba(243, 244, 246, 0.1)"),
        yaxis=dict(title="Fair Production Value ($ Millions)", gridcolor="rgba(243, 244, 246, 0.1)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark",
        height=580,
        margin=dict(l=40, r=40, t=80, b=40),
    )
    return fig


def render_trade_delta_cards(trade: Any) -> None:
    """Render side-by-side transaction impact cards for Team A and Team B."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"🛡️ {trade.team_a} Impact")
        st.markdown(f"**Outgoing:** {', '.join(trade.send_a)} (`${trade.salary_out_a:,.0f}`)")
        st.markdown(f"**Incoming:** {', '.join(trade.send_b)} (`${trade.salary_in_a:,.0f}`)")

        delta_a = trade.delta_a
        c1, c2 = st.columns(2)
        c1.metric(
            "Net Surplus Swing (ΔNSV)",
            f"${delta_a.delta_nsv:+,.0f}",
            delta=f"${delta_a.delta_nsv:,.0f}",
        )
        c2.metric(
            "Friction Drag Relief",
            f"${delta_a.friction_relief:+,.0f}",
            delta=f"${delta_a.friction_relief:,.0f}",
        )

        st.caption(
            f"Payroll: `${delta_a.pre_payroll:,.0f}` → `${delta_a.post_payroll:,.0f}` | **{delta_a.bracket_transition}**"
        )

        if trade.compliance_a.violations:
            for v in trade.compliance_a.violations:
                st.error(f"❌ {v}")
        else:
            st.success("✅ Team CBA Compliance Cleared")

    with col2:
        st.subheader(f"⚔️ {trade.team_b} Impact")
        st.markdown(f"**Outgoing:** {', '.join(trade.send_b)} (`${trade.salary_out_b:,.0f}`)")
        st.markdown(f"**Incoming:** {', '.join(trade.send_a)} (`${trade.salary_in_b:,.0f}`)")

        delta_b = trade.delta_b
        c3, c4 = st.columns(2)
        c3.metric(
            "Net Surplus Swing (ΔNSV)",
            f"${delta_b.delta_nsv:+,.0f}",
            delta=f"${delta_b.delta_nsv:,.0f}",
        )
        c4.metric(
            "Friction Drag Relief",
            f"${delta_b.friction_relief:+,.0f}",
            delta=f"${delta_b.friction_relief:,.0f}",
        )

        st.caption(
            f"Payroll: `${delta_b.pre_payroll:,.0f}` → `${delta_b.post_payroll:,.0f}` | **{delta_b.bracket_transition}**"
        )

        if trade.compliance_b.violations:
            for v in trade.compliance_b.violations:
                st.error(f"❌ {v}")
        else:
            st.success("✅ Team CBA Compliance Cleared")


def render_sensitivity_heatmap(df_sens: pd.DataFrame) -> go.Figure:
    """Render a 2D heatmap showing how trade surplus swings as lambda and $/WAR vary."""
    df_pivot = df_sens.pivot(index="cost_per_win_m", columns="lambda_scale", values="delta_nsv") / 1_000_000.0

    fig = go.Figure(
        data=go.Heatmap(
            z=df_pivot.values,
            x=[f"{x:.2f}x" for x in df_pivot.columns],
            y=[f"${y:.1f}M" for y in df_pivot.index],
            colorscale="RdYlGn",
            colorbar=dict(title="ΔNSV ($M)"),
            hovertemplate="Friction Scale: %{x}<br>Cost/Win: %{y}<br><b>Cleveland ΔNSV: $%{z:+.2f}M</b><extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>Cleveland Trade Surplus Sensitivity: λ Multiplier vs. $/WAR</b>",
            font=dict(size=16),
        ),
        xaxis=dict(title="Apron Friction Scale (0.0x = Pure Linear $/WAR, 1.0x = Baseline Hypothesis)"),
        yaxis=dict(title="Open-Market Cost Per Win ($ Millions)"),
        template="plotly_dark",
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def render_escape_frontier_chart(df_frontier: pd.DataFrame) -> go.Figure:
    """Render the break-even talent sacrifice curve comparing Linear $/WAR vs. Apron Friction."""
    fig = go.Figure()

    # Linear allowable WAR loss curve
    fig.add_trace(
        go.Scatter(
            x=df_frontier["salary_shed_m"],
            y=df_frontier["max_war_loss_linear"],
            mode="lines+markers",
            name="Linear $/WAR Frontier (Max Tolerable Loss)",
            line=dict(color="#EF4444", width=3, dash="dash"),
            marker=dict(size=8),
            hovertemplate="Salary Shed: $%{x}M<br><b>Linear Max WAR Loss: %{y:.2f} WAR</b><extra></extra>",
        )
    )

    # Apron allowable WAR loss curve
    fig.add_trace(
        go.Scatter(
            x=df_frontier["salary_shed_m"],
            y=df_frontier["max_war_loss_apron"],
            mode="lines+markers",
            name="Board Man Apron Frontier (4x Expanded Slack)",
            line=dict(color="#10B981", width=3.5),
            marker=dict(size=9),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.15)",
            hovertemplate=(
                "Salary Shed: $%{x}M<br>"
                "<b>Apron Max WAR Loss: %{y:.2f} WAR</b><br>"
                "<i>Trades in this shaded zone are rejected by linear models but accretive under apron math!</i><extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>Apron Escape Talent Sacrifice Frontier (Cleveland Second Apron Duck)</b>",
            font=dict(size=16),
        ),
        xaxis=dict(title="Salary Shed to Break Below 2nd Apron ($ Millions)"),
        yaxis=dict(title="Maximum Tolerable On-Court WAR Loss (Break-Even ΔNSV = $0)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark",
        height=420,
        margin=dict(l=40, r=40, t=70, b=40),
    )
    return fig
