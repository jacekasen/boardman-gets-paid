"""Streamlit Interactive Evaluator for Board Man Gets Paid."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Ensure repository root is on sys.path regardless of execution directory
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from app.components import (
        BRACKET_NAMES,
        render_surplus_scatter,
        render_trade_delta_cards,
    )
except ModuleNotFoundError:
    from components import (
        BRACKET_NAMES,
        render_surplus_scatter,
        render_trade_delta_cards,
    )
from boardman.case_studies import (
    run_cleveland_second_apron_trap,
    run_kawhi_circumvention_case_study,
    run_spurs_celtics_liquidity_swap,
)
from boardman.config import (
    CANONICAL_TEAM_NAMES,
    DEFAULT_SEASON,
    FIRST_APRON_2025_26,
    LUXURY_TAX_2025_26,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
    normalize_team,
)
from boardman.trade_engine import evaluate_trade
from boardman.valuation import (
    DEFAULT_COST_PER_WIN,
    build_league_surplus_board,
    calculate_player_valuation,
)

st.set_page_config(
    page_title="Board Man Gets Paid | NBA CBA Valuation Engine",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)
    return df_players, df_teams


df_players, df_teams = load_datasets()

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("🏀 Board Man Gets Paid")
st.sidebar.markdown(
    "*Pricing NBA production against modern CBA apron constraints & operational friction.*"
)

metric_choice = st.sidebar.selectbox(
    "Impact Metric Model",
    options=["war_vorp", "war_blend"],
    format_func=lambda x: "VORP-Calibrated WAR (2.70 * VORP)" if x == "war_vorp" else "Blended WAR (VORP + WS)",
)

cost_per_win = st.sidebar.slider(
    "Open-Market Cost Per Win ($M)",
    min_value=3.0,
    max_value=7.0,
    value=float(DEFAULT_COST_PER_WIN / 1_000_000.0),
    step=0.1,
) * 1_000_000.0

st.sidebar.divider()
st.sidebar.markdown("### 2025–26 CBA Thresholds")
st.sidebar.caption(f"**Salary Cap:** `${SALARY_CAP_2025_26:,.0f}`")
st.sidebar.caption(f"**Luxury Tax:** `${LUXURY_TAX_2025_26:,.0f}`")
st.sidebar.caption(f"**First Apron:** `${FIRST_APRON_2025_26:,.0f}`")
st.sidebar.caption(f"**Second Apron:** `${SECOND_APRON_2025_26:,.0f}`")
st.sidebar.divider()
st.sidebar.caption("Author: **Jace Kasen** | Open-Source Engine")

# Build live surplus board
df_board = build_league_surplus_board(
    df_players=df_players,
    df_teams=df_teams,
    metric_col=metric_choice,
    cost_per_win=cost_per_win,
)

# --- MAIN TABS ---
tab_board, tab_trade, tab_circumvention = st.tabs(
    ["📊 League Surplus Board", "🔄 CBA Trade Machine", "💼 'Uncle Dennis' Lab"]
)


# ==============================================================================
# TAB 1: LEAGUE SURPLUS BOARD
# ==============================================================================
with tab_board:
    st.header("NBA Contract Surplus & Apron Friction Explorer")
    st.markdown(
        "Standard valuation models assume linear efficiency. `boardman-gets-paid` introduces the **Apron Friction Tax ($\lambda$)** "
        "to penalize roster-inflexible contracts on high-payroll franchises."
    )

    # Top KPI Metrics
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_league_payroll = df_teams["total_payroll"].sum()
    kpi1.metric("League Active Payroll", f"${total_league_payroll:,.0f}")
    kpi2.metric("Calibrated $/WAR", f"${cost_per_win:,.0f}")
    kpi3.metric(
        "Apron Teams (Brackets 1–3)",
        f"{(df_teams['bracket'] > 0).sum()} / 30",
        help="Teams in Tax, 1st Apron, or 2nd Apron",
    )
    kpi4.metric(
        "2nd Apron Teams (Bracket 3)",
        f"{(df_teams['bracket'] == 3).sum()} (CLE)",
        delta="Max Friction λ=0.70",
        delta_color="inverse",
    )

    # Scatter Plot
    fig = render_surplus_scatter(df_board)
    st.plotly_chart(fig, use_container_width=True)

    # Leaderboard Tables
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("💎 Top 10 Best Value Contracts (Highest NSV)")
        top_steals = df_board.head(10)[
            ["player_name", "team", "salary", "war", "bracket", "fair_value", "net_surplus", "surplus_efficiency"]
        ].copy()
        top_steals["salary"] = top_steals["salary"].map("${:,.0f}".format)
        top_steals["fair_value"] = top_steals["fair_value"].map("${:,.0f}".format)
        top_steals["net_surplus"] = top_steals["net_surplus"].map("${:+,.0f}".format)
        top_steals["surplus_efficiency"] = top_steals["surplus_efficiency"].map("{:.2f}x".format)
        st.dataframe(top_steals, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("⚠️ Top 10 Most Inflexible Apron Drags (Salary > $15M)")
        overpays = (
            df_board[df_board["salary"] >= 15_000_000.0]
            .sort_values("net_surplus", ascending=True)
            .head(10)[
                ["player_name", "team", "salary", "war", "bracket", "friction_tax", "net_surplus"]
            ]
            .copy()
        )
        overpays["salary"] = overpays["salary"].map("${:,.0f}".format)
        overpays["friction_tax"] = overpays["friction_tax"].map("-${:,.0f}".format)
        overpays["net_surplus"] = overpays["net_surplus"].map("${:+,.0f}".format)
        st.dataframe(overpays, use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 2: INTERACTIVE TRADE MACHINE
# ==============================================================================
with tab_trade:
    st.header("CBA Trade Simulator & Surplus Swing Engine")
    st.markdown(
        "Evaluate transactions under statutory **2023 CBA rules** (matching bands, 1st apron hard-caps, 2nd apron aggregation bans) "
        "and calculate the resulting **Net Surplus Swing ($\Delta NSV$)**."
    )

    # Preset Scenario Buttons
    c_btn1, c_btn2, _ = st.columns([1, 1.2, 2])
    preset_trade = None
    if c_btn1.button("📌 Load Legal Swap (SAS ↔ BOS)"):
        preset_trade = ("SAS", ["Harrison Barnes", "Kelly Olynyk"], "BOS", ["Derrick White"])
    if c_btn2.button("🚫 Load 2nd Apron Violation (CLE ↔ BOS)"):
        preset_trade = ("CLE", ["Max Strus", "Dennis Schröder"], "BOS", ["Derrick White"])

    all_teams = sorted(df_teams["team"].unique())

    col_t1, col_t2 = st.columns(2)

    default_team_a = preset_trade[0] if preset_trade else "SAS"
    default_team_b = preset_trade[2] if preset_trade else "BOS"

    with col_t1:
        team_a = st.selectbox(
            "Select Team A",
            options=all_teams,
            index=all_teams.index(default_team_a),
            format_func=lambda x: f"{x} - {CANONICAL_TEAM_NAMES.get(x, x)}",
        )
        roster_a = df_players[df_players["team"] == team_a].sort_values("salary", ascending=False)
        default_send_a = preset_trade[1] if preset_trade and preset_trade[0] == team_a else []
        send_a = st.multiselect(
            f"Outgoing Players from {team_a}",
            options=roster_a["player_name"].tolist(),
            default=default_send_a,
        )

    with col_t2:
        other_teams = [t for t in all_teams if t != team_a]
        team_b_idx = other_teams.index(default_team_b) if default_team_b in other_teams else 0
        team_b = st.selectbox(
            "Select Team B",
            options=other_teams,
            index=team_b_idx,
            format_func=lambda x: f"{x} - {CANONICAL_TEAM_NAMES.get(x, x)}",
        )
        roster_b = df_players[df_players["team"] == team_b].sort_values("salary", ascending=False)
        default_send_b = preset_trade[3] if preset_trade and preset_trade[2] == team_b else []
        send_b = st.multiselect(
            f"Outgoing Players from {team_b}",
            options=roster_b["player_name"].tolist(),
            default=default_send_b,
        )

    if st.button("🚀 Evaluate Trade Transaction", type="primary", use_container_width=True):
        if not send_a or not send_b:
            st.warning("Please select at least one player to trade from each franchise.")
        else:
            try:
                trade_result = evaluate_trade(
                    team_a=team_a,
                    send_a=send_a,
                    team_b=team_b,
                    send_b=send_b,
                    df_players=df_players,
                    df_teams=df_teams,
                    cost_per_win=cost_per_win,
                    metric_col=metric_choice,
                )

                st.divider()
                if trade_result.is_legal:
                    st.success("### ✅ LEGAL 2023 CBA TRANSACTION")
                else:
                    st.error("### ❌ ILLEGAL CBA TRANSACTION")

                render_trade_delta_cards(trade_result)

                with st.expander("📄 View Full Trade Terminal Summary"):
                    st.code(trade_result.summary(), language="text")

            except Exception as e:
                st.error(f"Error evaluating trade: {e}")


# ==============================================================================
# TAB 3: "UNCLE DENNIS" CIRCUMVENTION LAB
# ==============================================================================
with tab_circumvention:
    st.header("The 'Board Man Gets Paid' Cap Circumvention Lab")
    st.markdown(
        "In **September 2026**, the NBA concluded its landmark investigation into the Los Angeles Clippers, "
        "imposing a **$30M fine** and stripping **five consecutive first-round picks (2029–2033)** for funneling "
        "improper off-the-cap income to Kawhi Leonard through 'no-show' corporate sponsorships."
    )

    st.info(
        "💡 **Economic Reality:** Off-the-cap income doesn't show up on Spotrac or HoopsHype, "
        "but it represents real economic investment by ownership. This lab prices the true Net Surplus of an asset "
        "when accounting for shadow compensation."
    )

    c_lab1, c_lab2 = st.columns([1, 1.2])

    with c_lab1:
        st.subheader("Shadow Compensation Slider")
        off_cap_cash = st.slider(
            "Annual Off-Cap Endorsement Deal ($ Millions)",
            min_value=0.0,
            max_value=25.0,
            value=7.0,
            step=0.5,
            help="E.g., The $28M / 4-year Aspiration financial services agreement ($7.0M/year).",
        ) * 1_000_000.0

        res = run_kawhi_circumvention_case_study(off_cap_cash=off_cap_cash)

        st.metric("Official On-the-Books Cap Hit", "$50,000,000")
        st.metric("Total Real Annual Cost", f"${50_000_000 + off_cap_cash:,.0f}")
        st.metric(
            "True Net Surplus Value (NSV)",
            f"${res['circumvented_nsv']:+,.0f}",
            delta=f"-${res['surplus_erosion']:,.0f} (Surplus Burned)",
            delta_color="inverse",
        )

    with c_lab2:
        st.subheader("Historic League Sanctions (Sept 2026)")
        st.markdown(
            """
            * **Franchise Penalty:** **$30 Million fine** (largest in NBA history).
            * **Draft Capital Forfeited:** **5 consecutive first-round picks** (2029, 2030, 2031, 2032, 2033).
            * **Executive Suspensions:**
                - Steve Ballmer (Owner): **1 year**
                - Gillian Zucker (Business Ops): **1 year**
                - Lawrence Frank (Basketball Ops): **6 months**
            * **Uncle Dennis Robertson:** **5-year league-wide ban** from all NBA business.
            * **Kawhi Leonard:** Fined **$700,000** in restitution; subsequently traded to Toronto.
            """
        )

        st.warning(
            "**Takeaway for Front Offices:** Under-the-table circumvention not only destroys asset surplus efficiency "
            "when caught—it permanently paralyzes a franchise's long-term draft optionality."
        )
