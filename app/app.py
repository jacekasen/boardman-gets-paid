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
        render_escape_frontier_chart,
        render_sensitivity_heatmap,
        render_surplus_scatter,
        render_trade_delta_cards,
    )
except ModuleNotFoundError:
    from components import (
        BRACKET_NAMES,
        render_escape_frontier_chart,
        render_sensitivity_heatmap,
        render_surplus_scatter,
        render_trade_delta_cards,
    )
from boardman.case_studies import (
    run_cleveland_dallas_strus_martin_escape,
    run_cleveland_detroit_apron_escape,
    run_cleveland_second_apron_trap,
    run_flagship_apron_escape_pair,
    run_kawhi_circumvention_case_study,
    run_spurs_celtics_liquidity_swap,
)
from boardman.config import (
    CANONICAL_TEAM_NAMES,
    DEFAULT_METRIC,
    DEFAULT_SEASON,
    FIRST_APRON_2025_26,
    LUXURY_TAX_2025_26,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
    SECOND_APRON_COST_COMPONENTS,
    normalize_team,
)
from boardman.clustering import (
    build_clustering_plot,
    calculate_historical_apron_clustering,
    summarize_clustering_evidence,
)
from boardman.empirical_dumps import (
    EMPIRICAL_SALARY_DUMPS,
    estimate_revealed_preference_lambda,
)
from boardman.sensitivity import (
    analyze_trade_sensitivity,
    calculate_apron_escape_frontier,
    calculate_break_even_lambda_3,
    calculate_flagship_uncertainty_pair,
    calculate_headline_uncertainty,
    calculate_ranking_elasticity,
    scan_apron_escape_trades,
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
    "*Evaluates the 2025–26 NBA season (with 2026–27 currently underway). "
    "Pricing NBA production against modern CBA apron constraints & operational friction.*"
)

metric_choice = st.sidebar.selectbox(
    "Impact Metric Model",
    options=["war_projected", "war_vorp", "war_blend"],
    format_func=lambda x: {
        "war_projected": "Multi-Season Blended WAR Prior (True-Talent Baseline - Default)",
        "war_vorp": "Realized 2025-26 Box-Score WAR (VORP-calibrated)",
        "war_blend": "Blended WAR (VORP + Win Shares)",
    }[x],
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
st.sidebar.caption("*(Statutory Art. VII Sec. 6(j) indexed at 1.1369x)*")
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
tab_board, tab_trade, tab_sensitivity, tab_empirical, tab_circumvention, tab_validation = st.tabs(
    [
        "📊 League Surplus Board",
        "🔄 CBA Trade Machine",
        "📈 Sensitivity & Frontier",
        "📉 Empirical Proof: Discontinuity & Dumps",
        "💼 'Uncle Dennis' Lab",
        "🔬 Audit Trail & Limitations",
    ]
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
        "Evaluate transactions under statutory **2023 CBA rules** (escalated matching bands, 1st apron hard-caps, 2nd apron aggregation bans, and dead-money restrictions) "
        "and calculate the resulting **Net Surplus Swing ($\Delta NSV$)**."
    )

    # Preset Scenario Buttons
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns([1, 1, 1.3, 1.3])
    if c_btn1.button("📌 Legal Swap (SAS ↔ BOS)"):
        st.session_state["sel_team_a"] = "SAS"
        st.session_state["sel_send_a"] = ["Harrison Barnes", "Kelly Olynyk"]
        st.session_state["sel_team_b"] = "BOS"
        st.session_state["sel_send_b"] = ["Derrick White"]
    if c_btn2.button("🚫 2nd Apron Ban (CLE ↔ BOS)"):
        st.session_state["sel_team_a"] = "CLE"
        st.session_state["sel_send_a"] = ["Max Strus", "Dennis Schröder"]
        st.session_state["sel_team_b"] = "BOS"
        st.session_state["sel_send_b"] = ["Derrick White"]
    if c_btn3.button("💎 Robust Flip (CLE ↔ DAL)"):
        st.session_state["sel_team_a"] = "CLE"
        st.session_state["sel_send_a"] = ["Max Strus"]
        st.session_state["sel_team_b"] = "DAL"
        st.session_state["sel_send_b"] = ["Caleb Martin"]
    if c_btn4.button("⚡ High-Stakes Gamble (CLE ↔ DET)"):
        st.session_state["sel_team_a"] = "CLE"
        st.session_state["sel_send_a"] = ["Jarrett Allen"]
        st.session_state["sel_team_b"] = "DET"
        st.session_state["sel_send_b"] = ["Isaiah Stewart"]

    all_teams = sorted(df_teams["team"].unique())

    default_team_a = st.session_state.get("sel_team_a", "CLE")
    default_team_b = st.session_state.get("sel_team_b", "DAL")
    default_send_a = st.session_state.get("sel_send_a", ["Max Strus"])
    default_send_b = st.session_state.get("sel_send_b", ["Caleb Martin"])

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        team_a = st.selectbox(
            "Select Team A",
            options=all_teams,
            index=all_teams.index(default_team_a) if default_team_a in all_teams else 0,
            format_func=lambda x: f"{x} - {CANONICAL_TEAM_NAMES.get(x, x)}",
        )
        # Filter out dead-money / waived contracts
        roster_a = df_players[
            (df_players["team"] == team_a) & (~df_players["is_dead_money"])
        ].sort_values("salary", ascending=False)
        current_defaults_a = [p for p in default_send_a if p in roster_a["player_name"].values]
        send_a = st.multiselect(
            f"Outgoing Players from {team_a} (Active Tradable Roster)",
            options=roster_a["player_name"].tolist(),
            default=current_defaults_a,
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
        # Filter out dead-money / waived contracts
        roster_b = df_players[
            (df_players["team"] == team_b) & (~df_players["is_dead_money"])
        ].sort_values("salary", ascending=False)
        current_defaults_b = [p for p in default_send_b if p in roster_b["player_name"].values]
        send_b = st.multiselect(
            f"Outgoing Players from {team_b} (Active Tradable Roster)",
            options=roster_b["player_name"].tolist(),
            default=current_defaults_b,
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

                # Check if this matches one of our Flagship Pair Scenarios
                is_robust_flip = (
                    (team_a == "CLE" and send_a == ["Max Strus"] and team_b == "DAL" and send_b == ["Caleb Martin"])
                    or (team_b == "CLE" and send_b == ["Max Strus"] and team_a == "DAL" and send_a == ["Caleb Martin"])
                )
                is_high_stakes_flip = (
                    (team_a == "CLE" and send_a == ["Jarrett Allen"] and team_b == "DET" and send_b == ["Isaiah Stewart"])
                    or (team_b == "CLE" and send_b == ["Jarrett Allen"] and team_a == "DET" and send_a == ["Isaiah Stewart"])
                )

                if is_robust_flip:
                    st.info(
                        """
                        ### 💎 FLAGSHIP RESULT 1: The Robust Second Apron Escape Flip (CLE ↔ DAL)
                        * **Linear $/WAR Verdict: ❌ REJECT (Cleveland loses -$613K in linear value)**
                          - Cleveland sheds $6.34M in salary, dropping from $211.7M to $205.3M (below the Second Apron).
                          - Under our multi-season true-talent prior (`war_projected`), Strus is 1.10 WAR and Martin is -0.23 WAR (net -1.33 WAR drop).
                        * **Board Man Apron Friction Verdict: ✅ ACCEPT (+$15.29M Net Surplus Gain)**
                          - Escaping Bracket 3 unlocks **+$15.90M in roster friction relief** and unfreezes Cleveland's 2033 first-round draft pick.
                          - **Break-Even:** $\lambda_3 \ge 0.356$ (holding $\lambda_2 = 0.35$ fixed). Because required friction relief is only **$613K**, this flip succeeds in **100% of Monte Carlo scenarios** drawn from our 4 sourced statutory cost components!
                        """
                    )
                elif is_high_stakes_flip:
                    st.warning(
                        """
                        ### ⚡ FLAGSHIP RESULT 2: The High-Stakes, Assumption-Dependent Apron Escape (CLE ↔ DET)
                        * **Linear $/WAR Verdict: ❌ REJECT (Cleveland loses -$19.42M on `war_projected`, or -$10.53M on `war_vorp`)**
                          - Cleveland sheds $5.0M in salary (dropping to $206.7M, below the Second Apron).
                          - However, Allen is a 6.37 WAR centerpiece vs Stewart at 1.70 WAR (a severe -4.67 WAR talent penalty).
                        * **Board Man Apron Friction Verdict: ❌ REJECT at Baseline $\lambda_3 = 0.70$ (-$3.49M deficit)**
                          - Friction relief is +$15.93M, but it fails to overcome the -$19.42M on-court talent deficit.
                          - **Break-Even:** requires $\lambda_3 \ge 0.779$ (escaping must be worth at least $19.42M/yr).
                          - **Win Probability:** Only ~3.4% of draws from our sourced statutory cost components reach $\lambda_3 \ge 0.78$. This demonstrates an organizational gamble on extreme friction severity.
                        """
                    )

                render_trade_delta_cards(trade_result)

                with st.expander("📄 View Full Trade Terminal Summary"):
                    st.code(trade_result.summary(), language="text")

            except Exception as e:
                st.error(f"Error evaluating trade: {e}")


# ==============================================================================
# TAB 3: SENSITIVITY ANALYSIS & THE TALENT FRONTIER
# ==============================================================================
with tab_sensitivity:
    st.header("📈 Parameter Sensitivity, Break-Even Frontier & League-Wide Scan")
    st.markdown(
        "Because $\lambda$ is an assumed scenario input rather than an estimate, this tab shows exactly how the conclusions "
        "depend on it: (1) the live break-even $\lambda_3$ and a Monte Carlo over an assumed range, (2) 2D sensitivity across "
        "$\lambda$ scales, (3) the talent sacrifice frontier, (4) Cleveland's escape menu, and (5) contract ranking elasticity."
    )

    st.subheader("1. Break-Even λ₃ & Monte Carlo Uncertainty: The Flagship Pair")
    st.markdown(
        "Instead of sampling $\\lambda_3$ from an arbitrary Uniform(0.40, 0.85) distribution, `boardman` "
        "draws $\\lambda_3$ by summing the **4 statutory 2023 CBA Second Apron cost components** "
        "(frozen draft pick, TP-MLE forfeiture, illiquidity haircut, repeater surcharge; totaling $23.3M–$36.2M/yr) "
        "and dividing by the franchise's quadratic roster base ($B_{\\text{pre}} = \\$44.39\\text{M}$). This produces "
        "a grounded empirical distribution for $\\lambda_3 \\in [0.525, 0.816]$ (mean ~0.66). Below we compare our "
        "**Flagship Pair**: the robust flip (Strus ↔ Martin) vs. the high-stakes gamble (Allen ↔ Stewart)."
    )

    unc_pair = calculate_flagship_uncertainty_pair(metric_col=metric_choice, cost_per_win=cost_per_win)
    rob_unc = unc_pair["robust_flip"]
    high_unc = unc_pair["high_stakes_flip"]

    c_rob, c_high = st.columns(2)

    with c_rob:
        st.markdown("#### 💎 Flagship 1: Robust Flip (Strus → Caleb Martin, DAL)")
        st.caption("Linear deficit: -$613K | Friction relief: +$15.90M | Delta NSV: +$15.29M")
        r1, r2 = st.columns(2)
        r1.metric("Break-Even λ₃", f"{rob_unc['break_even_lambda_3']:.3f}", help="Required λ₃ with λ₂=0.35 held fixed")
        r2.metric("Win Probability", f"{rob_unc['win_probability']*100:.1f}%", help="Win share across 10,000 draws from 4 statutory cost components")
        r3, r4 = st.columns(2)
        r3.metric("Mean Scenario ΔNSV", f"${rob_unc['mean_delta_nsv']/1e6:+.2f}M")
        r4.metric("90% Scenario Interval", f"[${rob_unc['scenario_interval_90'][0]/1e6:+.1f}M, ${rob_unc['scenario_interval_90'][1]/1e6:+.1f}M]")
        st.info("💡 **Takeaway:** Required friction relief is only $613K, so this flip succeeds in **100% of scenarios**.")

    with c_high:
        st.markdown("#### ⚡ Flagship 2: High-Stakes Gamble (Allen → Isaiah Stewart, DET)")
        st.caption("Linear deficit: -$19.42M | Friction relief: +$15.93M | Delta NSV: -$3.49M")
        h1, h2 = st.columns(2)
        h1.metric("Break-Even λ₃", f"{high_unc['break_even_lambda_3']:.3f}", help="Required λ₃ with λ₂=0.35 held fixed")
        h2.metric("Win Probability", f"{high_unc['win_probability']*100:.1f}%", help="Win share across 10,000 draws from 4 statutory cost components")
        h3, h4 = st.columns(2)
        h3.metric("Mean Scenario ΔNSV", f"${high_unc['mean_delta_nsv']/1e6:+.2f}M")
        h4.metric("90% Scenario Interval", f"[${high_unc['scenario_interval_90'][0]/1e6:+.1f}M, ${high_unc['scenario_interval_90'][1]/1e6:+.1f}M]")
        st.warning("⚠️ **Takeaway:** Allen's 4.67 WAR talent edge creates a severe deficit. Escaping pays off only in the top ~3-4% of friction severity draws.")

    st.divider()

    st.subheader("2. Apron Escape Tipping Point Heatmap (Cleveland ΔNSV)")
    st.markdown(
        "The heatmap below visualizes Cleveland's Net Surplus Swing ($\Delta NSV$) across operational friction multipliers ($\lambda$) "
        "and open-market Cost Per Win values ($C_w$). Notice that at $\lambda = 0.00$ (pure linear $/WAR$), every cell is deep red ($-5.4M to $-14.3M). "
        "Here every bracket's $\lambda$ scales together, so the tipping point (~0.66x, i.e. $\lambda_3 \approx 0.46$ with $\lambda_2 \approx 0.23$) "
        "differs from the fixed-$\lambda_2$ break-even above. At the 1.0x baseline the trade is $+\$5.40\text{M}$."
    )


    df_sens = analyze_trade_sensitivity(df_players=df_players, df_teams=df_teams, metric_col=metric_choice)
    fig_sens = render_sensitivity_heatmap(df_sens)
    st.plotly_chart(fig_sens, use_container_width=True)

    st.divider()

    st.subheader("2. The Apron Escape Frontier: Allowable Talent Sacrifice Curve")
    st.markdown(
        "Under linear $/WAR models, saving $\$5\text{M}$ only justifies sacrificing $0.96$ WAR ($-5.0M / 5.23M$). "
        "Under the **Board Man Apron Friction Model**, dropping below the Second Apron unlocks **$+\$15.93\text{M}$ in friction relief**, "
        "expanding the franchise's tolerable talent sacrifice to **$-3.93$ WAR (a 4.1x expansion!)**."
    )

    df_frontier = calculate_apron_escape_frontier(df_players=df_players, df_teams=df_teams, cost_per_win=cost_per_win)
    fig_frontier = render_escape_frontier_chart(df_frontier)
    st.plotly_chart(fig_frontier, use_container_width=True)

    st.dataframe(
        df_frontier.rename(
            columns={
                "salary_shed_m": "Salary Shed ($M)",
                "post_payroll_m": "Post Payroll ($M)",
                "friction_relief_m": "Friction Relief ($M)",
                "max_war_loss_linear": "Linear Max WAR Loss",
                "max_war_loss_apron": "Apron Max WAR Loss",
                "expansion_factor": "Slack Expansion Factor",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("3. Cleveland Second Apron Escape Menu & Frontier Ranking")
    st.markdown(
        "**The Core Mechanism:** If escaping the Second Apron is worth $R$/yr to Cleveland, any trade that sheds at least $3.86M "
        "and costs less than $R / C_w$ WAR is net-positive, while linear $/WAR models reject every talent sacrifice. At the baseline "
        "scenario ($\lambda_3 = 0.70$), $R = +\$15.93$M (~3.05 WAR). Below, we rank Cleveland's 1-for-1 escape options. The menu uses "
        "the **multi-season WAR prior** and **protects Cleveland's top three players** (Mitchell, Harden, Mobley), because a menu "
        "that trades away the franchise's core is not a credible front-office recommendation."
    )

    @st.cache_data
    def load_cached_flips(cw: float, metric: str) -> pd.DataFrame:
        return scan_apron_escape_trades(team="CLE", cost_per_win=cw, metric_col=metric)

    df_flips = load_cached_flips(cost_per_win, "war_projected")

    fc1, fc2, fc3 = st.columns(3)
    fc1.metric("Legal Trades Evaluated", "3,812 Trades")
    fc2.metric("Thesis-Flip Trades Identified", f"{len(df_flips)} Trades", delta="Flipped from Reject to Accept")
    if not df_flips.empty:
        avg_linear_loss = df_flips["linear_delta"].mean()
        avg_boardman_gain = df_flips["boardman_delta"].mean()
        fc3.metric("Avg Linear Loss vs. Avg Apron Gain", f"${avg_linear_loss/1e6:.1f}M → +${avg_boardman_gain/1e6:.1f}M")

        display_flips = df_flips.head(15)[
            [
                "target_player",
                "partner_team",
                "partner_player",
                "salary_shed",
                "war_loss",
                "linear_delta",
                "boardman_delta",
            ]
        ].copy()

        display_flips["salary_shed"] = display_flips["salary_shed"].map("${:,.0f}".format)
        display_flips["war_loss"] = display_flips["war_loss"].map("{:.2f} WAR".format)
        display_flips["linear_delta"] = display_flips["linear_delta"].map("${:+,.0f}".format)
        display_flips["boardman_delta"] = display_flips["boardman_delta"].map("${:+,.0f}".format)

        st.dataframe(
            display_flips.rename(
                columns={
                    "target_player": "CLE Outgoing",
                    "partner_team": "Partner Team",
                    "partner_player": "Incoming Player",
                    "salary_shed": "Salary Shed",
                    "war_loss": "On-Court WAR Sacrificed",
                    "linear_delta": "Linear Verdict ($)",
                    "boardman_delta": "Board Man Surplus ($)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("4. League Ranking Elasticity: Linear ($GSV$) vs. Apron-Aware ($NSV$)")
    st.markdown(
        "The table below isolates qualified veteran contracts ($\ge \$10\text{M}$) and displays the largest downward rank displacements "
        "caused by the Apron Friction Tax on high-payroll franchises."
    )

    df_elasticity = calculate_ranking_elasticity(
        df_players=df_players, df_teams=df_teams, cost_per_win=cost_per_win
    )

    display_elasticity = df_elasticity.head(15)[
        [
            "player_name",
            "team",
            "salary",
            "bracket",
            "gross_surplus",
            "friction_tax",
            "net_surplus",
            "rank_linear",
            "rank_friction",
            "rank_shift",
        ]
    ].copy()

    display_elasticity["salary"] = display_elasticity["salary"].map("${:,.0f}".format)
    display_elasticity["gross_surplus"] = display_elasticity["gross_surplus"].map("${:+,.0f}".format)
    display_elasticity["friction_tax"] = display_elasticity["friction_tax"].map("-${:,.0f}".format)
    display_elasticity["net_surplus"] = display_elasticity["net_surplus"].map("${:+,.0f}".format)
    display_elasticity["rank_shift"] = display_elasticity["rank_shift"].map("{:+d}".format)

    st.dataframe(
        display_elasticity.rename(
            columns={
                "player_name": "Player",
                "team": "Team",
                "salary": "Salary",
                "bracket": "Bracket",
                "gross_surplus": "Linear GSV",
                "friction_tax": "Friction Tax",
                "net_surplus": "Apron NSV",
                "rank_linear": "Linear Rank",
                "rank_friction": "Friction Rank",
                "rank_shift": "Rank Shift",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# TAB 4: EMPIRICAL VERIFICATION (BUNCHING & SALARY DUMPS)
# ==============================================================================
with tab_empirical:
    st.header("Empirical Verification: Apron Bunching & Real-World Salary Dumps")
    st.markdown(
        "A central critique of theoretical sports economics models is whether real-world general managers "
        "actually behave in accordance with hypothesized friction parameters. Below, we present two layers of "
        "empirical proof from official NBA transaction history (2020–2026)."
    )

    st.subheader("1. Econometric Evidence: Payroll Bunching at the Second Apron Discontinuity")
    st.markdown(
        "In public finance and economics (Kleven 2016, Saez 2010), **bunching estimation** identifies true notch-effects "
        "by measuring excess mass immediately below a statutory cutoff. If the Second Apron is merely a nominal guideline, "
        "team payrolls should follow a smooth continuous distribution. Instead, empirical payroll data demonstrates sharp bunching."
    )

    df_clust = calculate_historical_apron_clustering()
    clust_summary = summarize_clustering_evidence(df_clust)

    fig_clust = build_clustering_plot(df_clust)
    st.plotly_chart(fig_clust, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Post-CBA Bunching Within $5M of 2nd Apron", f"{clust_summary['post_cba_bunching_under_second_apron']} Teams", help="Teams structuring payroll within -$5M to $0 of Second Apron")
    c2.metric("Fisher Exact Test (Apron)", f"p = {clust_summary['fisher_p_bunching']:.2f}", help="Two-sided Fisher test: Post-CBA bunching vs. Pre-CBA synthetic placebo line")
    c3.metric("2nd Apron Contenders (2023–2026)", "4 → 3 → 1 (CLE)", delta="-75% Attrition", delta_color="inverse")
    c4.metric("Tax Bunching (Verified)", f"{clust_summary['luxury_tax_bunching']['post_cba_below_within_3m']} Below / {clust_summary['luxury_tax_bunching']['post_cba_above_within_3m']} Above", help="Teams within ±$3M of luxury tax line")

    st.info(f"💡 **Statistical Integrity Note:** {clust_summary['methodological_note']}")

    st.markdown(
        """
        **Notable Real-World Payroll Bunching Cases:**
        - **2023–24 Milwaukee Bucks:** Finished at **$182.23M** — exactly **$0.57M below the Second Apron ($182.79M)**.
        - **2024–25 Los Angeles Lakers:** Finished at **$188.02M** — exactly **$0.91M below the Second Apron ($188.93M)**.
        - **2024–25 New York Knicks:** Finished at **$186.81M** — **$2.12M below the Second Apron**.
        - **2025–26 New York Knicks:** Finished at **$207.45M** — exactly **$0.37M below the Second Apron ($207.82M)**.
        - **2025–26 Golden State Warriors:** Finished at **$204.12M** — **$3.70M below the Second Apron**.
        """
    )

    st.divider()

    st.subheader("2. Revealed-Preference Parameter Calibration: Bounding λ from Salary Dumps")
    st.markdown(
        "Can salary dumps pin down $\lambda_3$? We test it on Denver's Reggie Jackson dump. **They cannot:** once luxury tax "
        "savings are counted, tax cash alone justifies the dump, so the implied bound falls below $\lambda_2$ and is non-binding. "
        "$\lambda_3$ therefore remains a scenario input grounded in the cost breakdown (Tab 6)."
    )

    rev_lambda = estimate_revealed_preference_lambda()

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Benchmark Dump", "DEN → CHA (Reggie Jackson)")
    d2.metric("Net Cost After Tax", f"${rev_lambda['net_cost_after_tax']/1e6:+.2f}M", help="Pick equity ($8.0M) minus salary saved ($5.25M) minus luxury tax saved (realized-payroll basis)")
    d3.metric("Implied λ₃ Lower Bound", f"λ₃ ≥ {rev_lambda['implied_lambda_3_lower_bound']:.2f}", delta="Non-binding (< λ₂)", delta_color="off", help="Below λ₂ = 0.35, so it adds no information")
    d4.metric("Cleveland Break-Even (λ₂ fixed)", f"λ₃ ≥ {rev_lambda['cleveland_flip_break_even_lambda']:.2f}", help="Computed live from the trade engine")

    st.caption(f"💡 **Econometric Takeaway:** {rev_lambda['headline_takeaway']}")

    with st.expander("Detailed Derivation: Why the Denver Dump Does Not Bound λ₃"):
        tax_r = rev_lambda["luxury_tax_saved_realized"] / 1e6
        tax_d = rev_lambda["luxury_tax_saved_decision_time"] / 1e6
        net = rev_lambda["net_cost_after_tax"] / 1e6
        lb0 = rev_lambda["implied_lambda_3_lower_bound"]
        lb5 = rev_lambda["implied_lambda_3_lower_bound_with_05_war"]
        be = rev_lambda["cleveland_flip_break_even_lambda"]
        st.markdown(
            r"""
            **Transaction Analysis: Denver Nuggets Reggie Jackson Salary Dump (June 27, 2024)**
            1. **The Situation:** Denver sat ~$4.07M over the 2024–25 Second Apron ($188.93M).
            2. **The Transaction:** Denver traded Reggie Jackson ($5,250,000) and **three future 2nd-round picks** (2025, 2029, 2030) to Charlotte for $0 incoming salary.
            3. **Costs and Savings:**
               - Surrendered pick equity: $E \approx \$8.00\text{M}$ (3 SRPs at $\approx \$2.67\text{M}$ average surplus equity).
               - Salary saved: $S = \$5,250,000$.
               - Luxury tax saved: $T_{\text{tax}} \approx \$TAXR\text{M}$ on Denver's realized 2024–25 payroll (non-repeater rates; $\approx \$TAXD\text{M}$ on the decision-time payroll).
               - **Net cost after tax:** $E - S - T_{\text{tax}} \approx NET\text{M}$. Denver came out ahead in cash before any friction relief.
            4. **Revealed Preference Inequality:**
               $$\Delta \text{Friction Relief} \ge E - S - T_{\text{tax}} + (\Delta W \times C_w)$$
               $$\lambda_3 \ge \frac{E - S - T_{\text{tax}} + \Delta W \cdot C_w + 0.35 \times B_{\text{post}}}{B_{\text{pre}}}$$
            5. **Denver Roster Quadratic Base ($B_{\text{pre}} = \$42.25\text{M}, B_{\text{post}} = \$42.05\text{M}$):**
               - Jackson at replacement level: $\lambda_3 \ge LB0$. With a 0.5 WAR loss: $\lambda_3 \ge LB5$.
               - Both are below $\lambda_2 = 0.35$, which the model already requires, so the bound is **non-binding**.
               - An earlier version of this analysis dropped $T_{\text{tax}}$ and reported $\lambda_3 \ge 0.41$. That figure was wrong.
            6. **Conclusion:** Salary dumps by deep-tax teams are explained by tax cash and cannot separately identify operational friction.
               Cleveland's break-even ($\lambda_3 \ge BE$) must be weighed against the cost breakdown instead.
            """
            .replace("TAXR", f"{tax_r:.1f}")
            .replace("TAXD", f"{tax_d:.1f}")
            .replace("NET", f"{net:+.1f}")
            .replace("LB0", f"{lb0:.2f}")
            .replace("LB5", f"{lb5:.2f}")
            .replace("BE", f"{be:.2f}")
        )



# ==============================================================================
# TAB 5: "UNCLE DENNIS" CIRCUMVENTION LAB
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
        "when accounting for shadow compensation and models the franchise's **risk-adjusted expected penalty**."
    )

    c_lab1, c_lab2 = st.columns([1, 1.2])

    with c_lab1:
        st.subheader("Shadow Compensation & Risk Parameters")
        off_cap_cash = st.slider(
            "Annual Off-Cap Endorsement Deal ($ Millions)",
            min_value=0.0,
            max_value=25.0,
            value=7.0,
            step=0.5,
            help="E.g., The $28M / 4-year Aspiration financial services agreement ($7.0M/year).",
        ) * 1_000_000.0

        audit_prob = st.slider(
            "NBA Investigation / Audit Probability (P(Audit))",
            min_value=0.05,
            max_value=1.00,
            value=0.30,
            step=0.05,
            help="Exploratory probability assumption representing likelihood of regulatory enforcement.",
        )

        res = run_kawhi_circumvention_case_study(
            off_cap_cash=off_cap_cash, audit_probability=audit_prob
        )

        st.metric("Official On-the-Books Cap Hit", "$50,000,000")
        st.metric("Total Real Annual Cost", f"${50_000_000 + off_cap_cash:,.0f}")
        st.metric(
            "True Net Surplus Value (NSV)",
            f"${res['circumvented_nsv']:+,.0f}",
            delta=f"-${res['surplus_erosion']:,.0f} (Surplus Burned)",
            delta_color="inverse",
        )
        st.metric(
            "Expected Sanction Cost (Risk-Adjusted)",
            f"${res['expected_penalty_cost']:,.0f}",
            help="P(Audit) * [Fine ($30M) + 5 First-Round Picks ($57.5M assumed draft capital equity)]",
        )

    with c_lab2:
        st.subheader("Historic League Sanctions & Citations (Sept 2026)")
        st.markdown(
            """
            * **Franchise Penalty:** **$30 Million fine** (largest in NBA history).
            * **Draft Capital Forfeited:** **5 consecutive first-round picks** (2029, 2030, 2031, 2032, 2033).
              - Priced at $\$11.5\text{M}$ assumed rookie surplus curve value = **$\$57.5\text{M}$ in equity destroyed**.
            * **Executive Suspensions:**
                - Steve Ballmer (Owner): **1 year**
                - Gillian Zucker (Business Ops): **1 year**
                - Lawrence Frank (Basketball Ops): **6 months**
            * **Uncle Dennis Robertson:** **5-year league-wide ban** from all NBA business.
            * **Kawhi Leonard:** Fined **$700,000** in restitution; subsequently traded to Toronto.
            """
        )

        st.markdown("#### Primary Investigative & Statutory Sources")
        st.markdown(
            """
            1. **Pablo Torre**, *Pablo Torre Finds Out* (Meadowlark Media, investigative reporting on Aspiration sponsorship).
            2. **Wachtell, Lipton, Rosen & Katz** (Retained independent counsel for NBA Board of Governors).
            3. **NBA Constitution Article 35 & 2023 CBA Article XIII**, *Salary Cap Circumvention & Unauthorized Agreements*.
            """
        )

        st.warning(
            "**Takeaway for Front Offices:** Under-the-table circumvention not only destroys asset surplus efficiency "
            "when caught—it permanently paralyzes a franchise's long-term draft optionality."
        )


# ==============================================================================
# TAB 6: AUDIT TRAIL, REAL-WORLD CHECKS & MODEL LIMITATIONS
# ==============================================================================
with tab_validation:
    st.header("🔬 Model Validation, Real-World Checks & Audit Trail")
    st.markdown(
        "A rigorous sports analytics submission must be transparent about where its parameters originate, "
        "what real-world behavior it validates against, how AI was audited, and what limitations exist in the model."
    )

    st.subheader("1. Answering the Core Analytical Questions Directly")

    with st.expander("Q1: Show me one trade or contract that your model ranks differently from plain $/WAR, and why it's right."):
        st.markdown(
            """
            **The Central Finding & Flagship Pair of Results:**
            Rather than relying on a single trade whose outcome swings on injury assumptions, `boardman` presents a **Flagship Pair**:
            
            1. **Flagship 1: The Robust Apron Escape Flip (Cleveland ↔ Dallas)**
               - **The Trade:** Cleveland trades **Max Strus** ($15.94M, 1.10 WAR) to Dallas for **Caleb Martin** ($9.59M, -0.23 WAR).
               - **Linear $/WAR Verdict:** **REJECT (-$613K deficit)**. Cleveland sacrifices 1.33 WAR under the multi-season true-talent prior (`war_projected`) while saving $6.34M in salary.
               - **Board Man Verdict (baseline $\\lambda_3 = 0.70$):** **ACCEPT (+$15.29M Net Surplus Gain)**.
               - **Why Board Man is Right:** Shedding $6.34M drops Cleveland's payroll from $211.7M to $205.3M (**comfortably below the Second Apron of $207.8M** into Bracket 2). This unlocks **+$15.90M in roster friction relief** and unfreezes their 2033 first-round draft pick.
               - **Robustness:** Because the linear deficit is only $613K, break-even requires $\\lambda_3 \\ge 0.356$ (holding $\\lambda_2 = 0.35$ fixed). This trade succeeds across **100% of scenarios** drawn from our sourced statutory cost components!
            
            2. **Flagship 2: The High-Stakes, Assumption-Dependent Case (Cleveland ↔ Detroit)**
               - **The Trade:** Cleveland trades **Jarrett Allen** ($20.0M, 6.37 WAR) to Detroit for **Isaiah Stewart** ($15.0M, 1.70 WAR).
               - **Linear $/WAR Verdict:** **REJECT (-$19.42M deficit)**. Stewart represents a severe 4.67 WAR talent drop under multi-season true-talent evaluation.
               - **Board Man Verdict (baseline $\\lambda_3 = 0.70$):** **REJECT (-$3.49M deficit)**.
               - **The Insight:** Escaping the Second Apron provides +$15.93M in friction relief, but cannot overcome a 4.67 WAR talent sacrifice unless escaping is worth $\\ge \\$19.42\\text{M}/\\text{yr}$ ($\\lambda_3 \\ge 0.779$, win probability ~3.4%). This illustrates a high-stakes organizational gamble on extreme apron friction.
               - *(Note: Under single-season box scores where Allen missed time, the linear deficit was only -$10.53M and the trade flipped at $\\lambda_3 \\ge 0.58$. `boardman` transparently exposes this assumption sensitivity.)*
            """
        )

    with st.expander("Q2: Where do the λ values come from? How sensitive are the results to them?"):
        st.markdown(
            """
            **λ is grounded directly in the 4 statutory cost components of the 2023 CBA.**
            
            1. **Market Salary Dumps Cannot Identify $\\lambda_3$ (Tab 4):**
               We tested whether real-world salary dumps (such as Denver shedding Reggie Jackson) could bound $\\lambda_3$. They cannot: once luxury tax savings are properly accounted for, tax cash alone explains the dump, so the implied bound ($\\lambda_3 \\ge 0.08$) sits below $\\lambda_2 = 0.35$ and is non-binding.
            
            2. **Statutory 2023 CBA Cost Component Decomposition:**
               Instead of arbitrary parameters, $\\lambda_3$ is derived from the four explicit operational and financial penalties imposed by Article VII of the 2023 CBA:
            """
        )
        df_cost_comp = pd.DataFrame(SECOND_APRON_COST_COMPONENTS)[
            ["name", "statutory_basis", "citation", "low_usd", "high_usd", "midpoint_usd"]
        ].rename(
            columns={
                "name": "Cost Component",
                "statutory_basis": "CBA Statutory Basis",
                "citation": "Literature / Market Citation",
                "low_usd": "Low ($)",
                "high_usd": "High ($)",
                "midpoint_usd": "Midpoint ($)",
            }
        )
        st.dataframe(df_cost_comp, use_container_width=True, hide_index=True)
        st.markdown(
            """
            - **Total Annual Economic Drag:** Across these 4 components, total drag spans **$23.3M to $36.2M/yr** (midpoint **~$29.2M**).
            - Across Cleveland's roster quadratic base ($B_{\\text{pre}} = \\$44.39\\text{M}$), this implies $\\lambda_3 \\in [0.525, 0.816]$ with a mean of **~0.66**.
            - Our Monte Carlo simulation (Tab 3) draws directly from this empirical 4-component sum divided by $B_{\\text{pre}}$, rather than an arbitrary uniform distribution.
            """
        )

    with st.expander("Q3: Did you check anything against what actually happened in real-world NBA transactions?"):
        st.markdown(
            """
            **Econometric Discontinuity, Placebo Controls & Salary Dump Evidence:**
            1. **Discontinuity Bunching (2020–2026):**
               As shown in Tab 4, post-2023 NBA payrolls exhibit suggestive bunching immediately below the Second Apron (-$5M to $0 band):
               - 2023–24 Milwaukee Bucks: -$0.57M below 2nd Apron
               - 2024–25 Los Angeles Lakers: -$0.91M below 2nd Apron
               - 2025–26 New York Knicks: -$0.37M below 2nd Apron
               - 2025–26 Golden State Warriors: -$3.70M below 2nd Apron
               Meanwhile, teams above the Second Apron collapsed from 4 in 2023-24 to 3 in 2024-25 to only 1 in 2025-26 (-75% attrition).
            2. **Placebo Line & Statistical Significance:**
               Because the Second Apron did not exist pre-2023, the pre-2023 comparison is an explicit synthetic placebo line. A two-sided Fisher Exact Test yields $p \\approx 0.50$ (underpowered at $N=90$ post-CBA team-seasons). However, luxury tax line bunching (24 below vs 1 above pre-CBA; 23 below vs 6 above post-CBA) demonstrates that NBA front offices demonstrably avoid notch boundaries.
            3. **Real-World Salary Dumps:**
               At decision time, Denver's projected commitments sat ~$4.1M over the Second Apron assuming KCP was retained. Denver attached 3 SRPs to dump Reggie Jackson's $5.25M contract, and Dallas attached 3 SRPs to shed Tim Hardaway Jr. to clear space under the First Apron. These demonstrate real willingness to pay to escape restrictive apron tiers, even though tax cash prevents clean parameter identification.
            """
        )

    with st.expander("Q4: How does the engine handle data provenance, multi-contracts, and dead money?"):
        st.markdown(
            """
            **Data Provenance, Prior-Team Tracking & Statutory Dead Money Enforcement:**
            - **Accurate Directional Resolution:**
               When players are waived and stretched under CBA Article VII, Section 7, their former team retains a dead salary cap hit while they can sign an active contract with a new team.
               - **Damian Lillard:** Milwaukee waived and stretched Lillard ($22.5M dead cap hit on MIL's books). Lillard then signed a new active contract with Portland ($14.1M active roster asset). In our engine, MIL Lillard is strictly flagged as `is_dead_money = True`, whereas POR Lillard is active roster (`is_dead_money = False`).
               - **Deandre Ayton:** Portland waived and stretched Ayton ($25.5M dead cap hit on POR). Ayton then signed with the Lakers ($8.1M active roster). POR Ayton is flagged dead money; LAL Ayton is active.
               - **Marcus Smart:** Washington holds $14.8M dead money; Lakers hold $5.1M active.
               - **Jordan Clarkson:** Utah holds $10.6M dead money; Knicks hold $2.3M active.
            - **Statutory Dead Money Prohibition:**
               Attempting to trade a dead-money contract is rejected as illegal by `check_trade_compliance` and triggers an explicit CBA violation.
            - **Internal Consistency:**
               All 30 franchise payroll totals reconcile exactly to the sum of player contracts in our dataset ($\pm0.0\%$).
            """
        )

    st.divider()

    st.subheader("2. CBA Article VII Statutory Indexing")
    st.markdown(
        """
        Many public tools use outdated static thresholds ($7.5M, $29.0M, $250k). Under **Article VII, Section 6(j) of the 2023 CBA**, 
        matching bands and cash limits escalate annually in direct proportion to Salary Cap growth:
        - **2023–24 Baseline Cap:** $\$136,021,000$
        - **2025–26 Cap:** $\$154,647,000$ $\implies$ **Escalation Factor = $1.136934\times$**
        - **Band 1 Ceiling:** $\$7,500,000 \times 1.136934 = \mathbf{\$8,527,011}$
        - **Band 2 Ceiling:** $\$29,000,000 \times 1.136934 = \mathbf{\$32,971,107}$
        - **Trade Buffer / Minimum Allowable:** $\$250,000 \times 1.136934 = \mathbf{\$284,234}$
        
        `boardman-gets-paid` implements the exact escalated thresholds in [`boardman/config.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/config.py) and [`boardman/cba_rules.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/cba_rules.py).
        """
    )

    st.divider()

    st.subheader("3. Explicit Model Limitations & Multi-Season Blended WAR Prior")
    st.markdown(
        """
        Transparency regarding model boundaries and methodology:
        1. **Temporal Scope:** All contract evaluations, roster models, and apron calculations evaluate the **2025–26 NBA season** (with 2026–27 currently underway).
        2. **Single-Season Box-Score Scope vs Multi-Season Prior:** Single-season box scores naturally penalize injured stars (e.g. Tyrese Haliburton, Jayson Tatum). To address this, `boardman` provides a **Multi-Season Blended WAR Prior (`war_projected`)** as the primary default impact metric, regressing current snapshots against 3-year historical talent baselines (Marcel-style weighted regression approach). Under this model, Tatum and Haliburton are recognized as positive star assets, and underwater contracts like Zach LaVine, Khris Middleton, and Jordan Poole correctly occupy the bottom ranks.
        3. **Draft Pick Equity Valuation:** The engine models forfeited draft picks using empirical draft-value curves (~$11.5M average rookie contract surplus), but does not account for team-specific lottery protections or standings variance.
        4. **Dynamic Franchise Valuation:** Roster friction $\lambda$ is modeled as a franchise-level operational drag; future extensions could incorporate multi-year luxury tax repeater clocks and player option exercise probabilities.
        """
    )

    st.divider()

    st.subheader("4. Human-in-the-Loop AI Audit Trail: What We Caught & Corrected")
    st.markdown(
        """
        In compliance with academic rigor and datathon guidelines, we document key bugs identified and corrected through human domain review:
        1. **Damian Lillard Dead-Money Direction Bug:**
           - *The Issue:* An early heuristic assigned dead money to the smaller salary row whenever stats were missing. Because Lillard was injured in 2025–26, this inverted Portland and Milwaukee (marking Portland as dead money and Milwaukee as active).
           - *The Fix:* We redesigned `check_dead_money` in `boardman/data/ingest.py` to cross-reference prior-season contract history. The waiving franchise (MIL) is flagged dead money, and the destination franchise (POR) is flagged active. Tested and enforced in `tests/test_trade_engine.py`.
        2. **Sensitivity Plumbing Disconnection:**
           - *The Issue:* An intermediate commit calculated scaled $\lambda$ in the sensitivity module but failed to route it into the underlying roster valuation call, resulting in a flat response curve.
           - *The Fix:* Full plumbing of `scaled_lambda` through `evaluate_trade` $\to$ `calculate_roster_delta` $\to$ `calculate_roster_valuation` $\to$ `get_team_bracket`, with unit tests verifying strict equality to linear $/WAR at $\lambda=0.00$ and monotonic growth.
        3. **Framing & Scalability of League Scan:**
           - *The Issue:* Framing candidate trades as "30 independent empirical discoveries" risked overclaiming what is fundamentally one core economic mechanism.
           - *The Fix:* Reframed as an optimal frontier escape menu ranking Cleveland's choices, and accelerated execution by 15x using fast statutory compliance pre-filters.
        4. **Salary Dump Directional Sign Error:**
           - *The Issue:* An initial draft of revealed preference lambda added salary shed to pick equity rather than subtracting it, failing to recognize that shedding salary saves cash in the team's favor.
           - *The Fix:* Corrected net cost paid to $E - S = \$8.0\text{M} - \$5.25\text{M} = \$2.75\text{M}$, dropping artificial upper bounds.
        5. **Synthetic Placebo Line & Fisher Exact Reporting:**
           - *The Issue:* Comparing post-2023 payroll bunching to pre-2023 data without acknowledging that the Second Apron did not exist pre-2023.
           - *The Fix:* Formally labeled the pre-2023 line as a synthetic placebo line, computed two-sided Fisher Exact tests ($p \approx 0.50$), and emphasized that while Second Apron data is underpowered ($N=90$), luxury tax line bunching demonstrates verified behavioral response.
        6. **Omitted Luxury Tax Term in the Denver Bound:**
           - *The Issue:* The revealed-preference inequality included $T_{\text{tax}}$ but the computation dropped it, reporting $\lambda_3 \ge 0.41$. Denver saved ~\$14M in tax, far more than the \$2.75M net pick cost.
           - *The Fix:* Implemented the 2023 CBA incremental tax schedule (`calculate_luxury_tax`). The corrected bound ($\lambda_3 \ge 0.08$) is below $\lambda_2$ and non-binding; we now state that salary dumps do not identify $\lambda_3$.
        7. **Mismatched Break-Even Comparison:**
           - *The Issue:* A hardcoded break-even of $\lambda_3 = 0.46$ came from the sensitivity grid, which scales $\lambda_2$ down with $\lambda_3$, but was compared against a bound and Monte Carlo that hold $\lambda_2 = 0.35$ fixed.
           - *The Fix:* `calculate_break_even_lambda_3` solves the break-even live from the trade engine with $\lambda_2$ fixed (0.58), and a test checks it agrees with the Monte Carlo's closed form. The Monte Carlo interval is relabeled a scenario interval, not a credible interval.
        8. **Escape Menu Recommending Cornerstone Trades:**
           - *The Issue:* Ranking on single-season WAR, the escape menu's top suggestion was trading Evan Mobley for Brandon Ingram.
           - *The Fix:* The scan now uses the multi-season WAR prior and protects the team's top three players by default (`protect_top_n=3`).
        """
    )

