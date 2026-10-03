"""Sensitivity analysis engine: Evaluates parameter elasticity across lambda and Cost-Per-Win grids,
scans league-wide apron-escape trades, and models the break-even talent frontier.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel

from boardman.cba_rules import check_trade_compliance
from boardman.config import (
    DEFAULT_SEASON,
    FRICTION_LAMBDA,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
)
from boardman.trade_engine import TradeEvaluation, evaluate_trade
from boardman.valuation import (
    DEFAULT_COST_PER_WIN,
    build_league_surplus_board,
    calculate_roster_delta,
)


class SensitivityPoint(BaseModel):
    lambda_scale: float
    cost_per_win: float
    cleveland_delta_nsv: float
    is_cleveland_positive: bool
    linear_verdict_flipped: bool


def analyze_trade_sensitivity(
    team_a: str = "CLE",
    send_a: list[str] | None = None,
    team_b: str = "DET",
    send_b: list[str] | None = None,
    lambda_scales: list[float] | None = None,
    cost_per_win_range: list[float] | None = None,
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    metric_col: str = "war_vorp",
) -> pd.DataFrame:
    """Evaluate how a trade's surplus delta swings across a 2D parameter grid of lambda and Cost-Per-Win.

    Directly passes scaled_lambda into evaluate_trade so that at lambda_scale = 0.0,
    the model mathematically collapses to pure linear $/WAR (friction = 0).
    """
    if send_a is None:
        send_a = ["Jarrett Allen"]
    if send_b is None:
        send_b = ["Isaiah Stewart"]

    if lambda_scales is None:
        lambda_scales = [0.0, 0.25, 0.50, 0.75, 1.0, 1.25, 1.5, 2.0]
    if cost_per_win_range is None:
        cost_per_win_range = [3_500_000.0, 4_500_000.0, 5_229_872.0, 6_000_000.0, 6_500_000.0]

    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    # Dynamically look up outgoing and incoming WAR
    roster_a = df_players[df_players["team"] == team_a]
    roster_b = df_players[df_players["team"] == team_b]

    war_map_a = roster_a.set_index("player_name")[metric_col].to_dict()
    war_map_b = roster_b.set_index("player_name")[metric_col].to_dict()

    war_out = sum(war_map_a.get(p, 0.0) for p in send_a)
    war_in = sum(war_map_b.get(p, 0.0) for p in send_b)
    war_delta = war_in - war_out

    results: list[dict[str, Any]] = []

    for lam_scale in lambda_scales:
        # Scale friction lambda across all brackets
        scaled_lambda = {k: v * lam_scale for k, v in FRICTION_LAMBDA.items()}

        for cw in cost_per_win_range:
            # Evaluate trade with the custom scaled_lambda dictionary
            trade = evaluate_trade(
                team_a=team_a,
                send_a=send_a,
                team_b=team_b,
                send_b=send_b,
                df_players=df_players,
                df_teams=df_teams,
                cost_per_win=cw,
                metric_col=metric_col,
                friction_lambda=scaled_lambda,
            )

            # Linear delta is: salary saved + (war delta * cw)
            salary_saved = trade.salary_out_a - trade.salary_in_a
            linear_delta = salary_saved + (war_delta * cw)

            delta_nsv = trade.delta_a.delta_nsv
            friction_relief = trade.delta_a.friction_relief

            results.append(
                {
                    "lambda_scale": lam_scale,
                    "cost_per_win": cw,
                    "cost_per_win_m": round(cw / 1_000_000.0, 2),
                    "delta_nsv": round(delta_nsv, 2),
                    "friction_relief": round(friction_relief, 2),
                    "is_positive": delta_nsv > 0,
                    "linear_delta": round(linear_delta, 2),
                    "verdict_flipped": bool((linear_delta < 0) and (delta_nsv > 0)),
                }
            )

    return pd.DataFrame(results)


def scan_apron_escape_trades(
    team: str = "CLE",
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    metric_col: str = "war_vorp",
) -> pd.DataFrame:
    """Scan all legal 1-for-1 trades where an apron team sheds enough salary to drop below an apron threshold,
    identifying trades where the verdict flips from Linear Reject to Board Man Accept.
    """
    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    team_row = df_teams[df_teams["team"] == team]
    if team_row.empty:
        return pd.DataFrame()

    total_payroll = float(team_row["total_payroll"].iloc[0])
    threshold = SECOND_APRON_2025_26
    apron_excess = total_payroll - threshold

    if apron_excess <= 0:
        return pd.DataFrame()

    # Get non-dead-money players on the target team with salary > excess
    target_players = df_players[
        (df_players["team"] == team)
        & (~df_players["is_dead_money"])
        & (df_players["salary"] > apron_excess)
    ]

    other_teams = [t for t in df_teams["team"].unique() if t != team]
    flips: list[dict[str, Any]] = []

    team_b_payrolls = df_teams.set_index("team")["total_payroll"].to_dict()

    for _, p_out in target_players.iterrows():
        p_out_name = str(p_out["player_name"])
        p_out_sal = float(p_out["salary"])
        p_out_war = float(p_out[metric_col])

        for other_t in other_teams:
            cand_players = df_players[
                (df_players["team"] == other_t)
                & (~df_players["is_dead_money"])
                & (df_players["salary"] <= (p_out_sal - apron_excess))
            ]
            b_payroll = team_b_payrolls.get(other_t, 0.0)

            for _, p_in in cand_players.iterrows():
                p_in_name = str(p_in["player_name"])
                p_in_sal = float(p_in["salary"])
                salary_shed = p_out_sal - p_in_sal
                if salary_shed < apron_excess:
                    continue

                # Fast statutory CBA compliance pre-filter on partner team
                comp_b = check_trade_compliance(
                    team_code=other_t,
                    pre_payroll=b_payroll,
                    outgoing_contracts=[p_in_sal],
                    incoming_contracts=[p_out_sal],
                )
                if not comp_b.is_compliant:
                    continue

                p_in_war = float(p_in[metric_col])

                try:
                    res = evaluate_trade(
                        team_a=team,
                        send_a=[p_out_name],
                        team_b=other_t,
                        send_b=[p_in_name],
                        df_players=df_players,
                        df_teams=df_teams,
                        cost_per_win=cost_per_win,
                        metric_col=metric_col,
                    )
                    if res.is_legal:
                        war_delta = p_in_war - p_out_war
                        linear_delta = salary_shed + (war_delta * cost_per_win)
                        boardman_delta = res.delta_a.delta_nsv

                        # Did the verdict flip from linear reject to apron accept?
                        if linear_delta < 0 and boardman_delta > 0:
                            flips.append(
                                {
                                    "target_player": p_out_name,
                                    "target_salary": p_out_sal,
                                    "target_war": p_out_war,
                                    "partner_team": other_t,
                                    "partner_player": p_in_name,
                                    "partner_salary": p_in_sal,
                                    "partner_war": p_in_war,
                                    "salary_shed": round(salary_shed, 2),
                                    "war_loss": round(p_out_war - p_in_war, 2),
                                    "linear_delta": round(linear_delta, 2),
                                    "boardman_delta": round(boardman_delta, 2),
                                    "friction_relief": round(res.delta_a.friction_relief, 2),
                                }
                            )
                except Exception:
                    continue

    df_flips = pd.DataFrame(flips)
    if not df_flips.empty:
        df_flips = df_flips.sort_values("boardman_delta", ascending=False).reset_index(drop=True)
    return df_flips


def calculate_apron_escape_frontier(
    team: str = "CLE",
    salary_shed_steps: list[float] | None = None,
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
) -> pd.DataFrame:
    """Calculate the theoretical break-even talent frontier: allowable WAR loss vs salary shed.

    Compares the maximum tolerable talent drop under linear $/WAR vs. the Apron Friction model.
    """
    if salary_shed_steps is None:
        salary_shed_steps = [4_000_000.0, 5_000_000.0, 6_000_000.0, 8_000_000.0, 10_000_000.0]

    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    team_row = df_teams[df_teams["team"] == team]
    payroll = float(team_row["total_payroll"].iloc[0]) if not team_row.empty else 211_686_176.0

    # Roster players
    roster = df_players[df_players["team"] == team].to_dict(orient="records")

    frontier_points: list[dict[str, Any]] = []

    for shed in salary_shed_steps:
        post_payroll = payroll - shed

        # Compute delta with zero player talent change to isolate pure friction relief
        delta = calculate_roster_delta(
            team_code=team,
            pre_roster=roster,
            post_roster=roster,
            pre_payroll=payroll,
            post_payroll=post_payroll,
            cost_per_win=cost_per_win,
        )

        friction_relief = delta.friction_relief

        # Break-even allowable WAR loss (Delta NSV = 0):
        # Linear: salary_shed + (Delta_W * C_w) = 0 => Delta_W = -salary_shed / C_w
        max_war_loss_linear = -(shed / cost_per_win)

        # Apron: salary_shed + friction_relief + (Delta_W * C_w) = 0 => Delta_W = -(salary_shed + friction_relief) / C_w
        max_war_loss_apron = -((shed + friction_relief) / cost_per_win)

        expansion_factor = (
            (max_war_loss_apron / max_war_loss_linear) if max_war_loss_linear != 0 else 1.0
        )

        frontier_points.append(
            {
                "salary_shed": shed,
                "salary_shed_m": round(shed / 1_000_000.0, 2),
                "post_payroll_m": round(post_payroll / 1_000_000.0, 2),
                "friction_relief_m": round(friction_relief / 1_000_000.0, 2),
                "max_war_loss_linear": round(max_war_loss_linear, 2),
                "max_war_loss_apron": round(max_war_loss_apron, 2),
                "expansion_factor": round(expansion_factor, 2),
            }
        )

    return pd.DataFrame(frontier_points)


def calculate_ranking_elasticity(
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
) -> pd.DataFrame:
    """Measure how player contract rankings diverge between linear ($GSV) and apron-friction ($NSV) models."""
    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    df_board = build_league_surplus_board(
        df_players=df_players,
        df_teams=df_teams,
        cost_per_win=cost_per_win,
    )

    df_active = df_board[df_board["salary"] >= 10_000_000.0].copy()
    df_active["rank_linear"] = df_active["gross_surplus"].rank(ascending=False).astype(int)
    df_active["rank_friction"] = df_active["net_surplus"].rank(ascending=False).astype(int)
    df_active["rank_shift"] = df_active["rank_linear"] - df_active["rank_friction"]

    # Sort by largest downward penalty caused by the apron friction tax
    return df_active.sort_values("friction_tax", ascending=False).reset_index(drop=True)
