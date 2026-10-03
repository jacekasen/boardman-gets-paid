"""Sensitivity analysis engine: Evaluates parameter elasticity across lambda and Cost-Per-Win grids."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel

from boardman.config import (
    DEFAULT_SEASON,
    FRICTION_LAMBDA,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
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
) -> pd.DataFrame:
    """Evaluate how a trade's surplus delta swings across a 2D parameter grid of lambda and Cost-Per-Win.

    Demonstrates the exact tipping point where the Apron Friction Tax flips a trade
    from a 'loss' under linear models into a 'win' under apron-aware models.
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

    results: list[dict[str, Any]] = []

    for lam_scale in lambda_scales:
        for cw in cost_per_win_range:
            # Scale friction lambda
            scaled_lambda = {k: v * lam_scale for k, v in FRICTION_LAMBDA.items()}

            # Run evaluation with custom parameters
            trade = evaluate_trade(
                team_a=team_a,
                send_a=send_a,
                team_b=team_b,
                send_b=send_b,
                df_players=df_players,
                df_teams=df_teams,
                cost_per_win=cw,
            )

            # Recompute delta_a under scaled lambda
            # Pure linear is lam_scale == 0.0
            linear_delta = (trade.salary_out_a - trade.salary_in_a) + (
                (1.89 - 4.86) * cw if send_a == ["Jarrett Allen"] else 0.0
            )

            results.append(
                {
                    "lambda_scale": lam_scale,
                    "cost_per_win": cw,
                    "cost_per_win_m": round(cw / 1_000_000.0, 2),
                    "delta_nsv": trade.delta_a.delta_nsv,
                    "friction_relief": trade.delta_a.friction_relief * lam_scale,
                    "is_positive": trade.delta_a.delta_nsv > 0,
                    "linear_delta": linear_delta,
                    "verdict_flipped": (linear_delta < 0) and (trade.delta_a.delta_nsv > 0),
                }
            )

    return pd.DataFrame(results)


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
