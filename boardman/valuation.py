"""Core valuation engine: Fair Production Value, Gross Surplus, Apron Friction Tax, and Net Surplus Value."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from boardman.config import (
    DEFAULT_SEASON,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
    get_team_bracket,
    normalize_team,
)

DEFAULT_COST_PER_WIN = 5_229_871.98  # Calibrated 2025-26 unconstrained veteran $/WAR


class PlayerValuation(BaseModel):
    """Detailed contract valuation and surplus metrics for an individual player."""

    player_id: str
    player_name: str
    team: str
    salary: float
    cap_share: float
    war: float
    cost_per_win: float
    fair_value: float
    gross_surplus: float
    bracket: int
    lambda_tax: float
    friction_tax: float
    net_surplus: float
    surplus_efficiency: float = Field(description="Net Surplus per dollar of cap hit (NSV / Salary)")
    uncle_dennis_cash: float = Field(default=0.0, description="Hypothetical off-the-cap circumvention cash")


class TeamValuation(BaseModel):
    """Franchise-level roster payroll, total production value, aggregate friction drag, and net surplus."""

    team: str
    season: str = DEFAULT_SEASON
    total_payroll: float
    bracket: int
    lambda_tax: float
    total_fair_value: float
    total_gross_surplus: float
    total_friction_tax: float
    total_net_surplus: float
    roster_size: int
    players: list[PlayerValuation] = Field(default_factory=list)


class RosterDelta(BaseModel):
    """Comparison of team valuation state before and after a proposed roster change or trade."""

    team: str
    pre_payroll: float
    post_payroll: float
    payroll_change: float
    pre_bracket: int
    post_bracket: int
    bracket_transition: str
    pre_net_surplus: float
    post_net_surplus: float
    delta_nsv: float
    friction_relief: float


def compute_apron_friction(
    cap_hit: float,
    team_payroll: float,
    salary_cap: float = SALARY_CAP_2025_26,
) -> tuple[int, float, float]:
    """Calculate the Apron Friction Tax for a contract given the team's payroll and bracket.

    Returns:
        tuple of (bracket: int, lambda_tax: float, friction_tax: float)
    """
    if cap_hit <= 0:
        bracket, lambda_tax = get_team_bracket(team_payroll)
        return bracket, lambda_tax, 0.0

    bracket, lambda_tax = get_team_bracket(team_payroll)
    # Quadratic drag: lambda * cap_hit * (cap_hit / salary_cap)
    friction = lambda_tax * cap_hit * (cap_hit / salary_cap)
    return bracket, lambda_tax, friction


def calculate_player_valuation(
    player: dict[str, Any] | BaseModel,
    team_payroll: float,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = "war_vorp",
    uncle_dennis_cash: float = 0.0,
) -> PlayerValuation:
    """Evaluate an individual player's Fair Production Value, GSV, Friction Tax, and NSV."""
    data = player.model_dump() if isinstance(player, BaseModel) else dict(player)

    player_id = str(data.get("player_id", "unknown"))
    player_name = str(data.get("player_name", "Unknown Player"))
    team = normalize_team(str(data.get("team", "FA")))
    cap_hit = float(data.get("salary", 0.0))
    cap_share = float(data.get("cap_share", (cap_hit / salary_cap) * 100.0 if salary_cap > 0 else 0.0))
    war = float(data.get(metric_col, data.get("war_vorp", 0.0)))

    # Fair Production Value
    fair_value = war * cost_per_win

    # Gross Surplus Value (FV - Cap Hit - any off-cap cash)
    effective_cost = cap_hit + uncle_dennis_cash
    gross_surplus = fair_value - effective_cost

    # Apron Friction Tax
    bracket, lambda_tax, friction_tax = compute_apron_friction(cap_hit, team_payroll, salary_cap=salary_cap)

    # Net Surplus Value
    net_surplus = gross_surplus - friction_tax

    # Efficiency: NSV per dollar
    surplus_efficiency = (net_surplus / cap_hit) if cap_hit > 0 else 0.0

    return PlayerValuation(
        player_id=player_id,
        player_name=player_name,
        team=team,
        salary=cap_hit,
        cap_share=cap_share,
        war=round(war, 2),
        cost_per_win=cost_per_win,
        fair_value=round(fair_value, 2),
        gross_surplus=round(gross_surplus, 2),
        bracket=bracket,
        lambda_tax=lambda_tax,
        friction_tax=round(friction_tax, 2),
        net_surplus=round(net_surplus, 2),
        surplus_efficiency=round(surplus_efficiency, 3),
        uncle_dennis_cash=round(uncle_dennis_cash, 2),
    )


def calculate_roster_valuation(
    players: list[dict[str, Any] | BaseModel],
    team_payroll: float | None = None,
    team_code: str = "TEAM",
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = "war_vorp",
) -> TeamValuation:
    """Aggregate fair values, gross surplus, friction penalties, and net surplus across a full roster."""
    player_dicts = [p.model_dump() if isinstance(p, BaseModel) else dict(p) for p in players]

    # If team_payroll is omitted, compute sum of player cap hits
    if team_payroll is None:
        team_payroll = sum(float(p.get("salary", 0.0)) for p in player_dicts)

    bracket, lambda_tax = get_team_bracket(team_payroll)

    valuations: list[PlayerValuation] = []
    total_fv = 0.0
    total_gsv = 0.0
    total_friction = 0.0
    total_nsv = 0.0

    for p in player_dicts:
        val = calculate_player_valuation(
            p,
            team_payroll=team_payroll,
            cost_per_win=cost_per_win,
            salary_cap=salary_cap,
            metric_col=metric_col,
        )
        valuations.append(val)
        total_fv += val.fair_value
        total_gsv += val.gross_surplus
        total_friction += val.friction_tax
        total_nsv += val.net_surplus

    return TeamValuation(
        team=team_code,
        total_payroll=round(team_payroll, 2),
        bracket=bracket,
        lambda_tax=lambda_tax,
        total_fair_value=round(total_fv, 2),
        total_gross_surplus=round(total_gsv, 2),
        total_friction_tax=round(total_friction, 2),
        total_net_surplus=round(total_nsv, 2),
        roster_size=len(valuations),
        players=valuations,
    )


def calculate_roster_delta(
    team_code: str,
    pre_roster: list[dict[str, Any] | BaseModel],
    post_roster: list[dict[str, Any] | BaseModel],
    pre_payroll: float | None = None,
    post_payroll: float | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = "war_vorp",
) -> RosterDelta:
    """Compute franchise-level surplus delta (Delta NSV) resulting from a roster transaction.

    Captures both:
    1. Direct player talent/salary swap surplus.
    2. Roster-wide friction relief if the transaction changes the team's apron bracket.
    """
    pre_val = calculate_roster_valuation(
        pre_roster,
        team_payroll=pre_payroll,
        team_code=team_code,
        cost_per_win=cost_per_win,
        salary_cap=salary_cap,
        metric_col=metric_col,
    )

    post_val = calculate_roster_valuation(
        post_roster,
        team_payroll=post_payroll,
        team_code=team_code,
        cost_per_win=cost_per_win,
        salary_cap=salary_cap,
        metric_col=metric_col,
    )

    delta_nsv = post_val.total_net_surplus - pre_val.total_net_surplus
    friction_relief = pre_val.total_friction_tax - post_val.total_friction_tax
    payroll_change = post_val.total_payroll - pre_val.total_payroll

    transition_str = f"Bracket {pre_val.bracket} -> Bracket {post_val.bracket}"
    if pre_val.bracket != post_val.bracket:
        transition_str += " (BRACKET SHIFT)"

    return RosterDelta(
        team=team_code,
        pre_payroll=pre_val.total_payroll,
        post_payroll=post_val.total_payroll,
        payroll_change=round(payroll_change, 2),
        pre_bracket=pre_val.bracket,
        post_bracket=post_val.bracket,
        bracket_transition=transition_str,
        pre_net_surplus=pre_val.total_net_surplus,
        post_net_surplus=post_val.total_net_surplus,
        delta_nsv=round(delta_nsv, 2),
        friction_relief=round(friction_relief, 2),
    )


def build_league_surplus_board(
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    metric_col: str = "war_vorp",
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
) -> pd.DataFrame:
    """Build full league leaderboard of player valuations, Gross Surplus, Friction, and Net Surplus."""
    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    team_payrolls = df_teams.set_index("team")["total_payroll"].to_dict()

    valuations = []
    for _, row in df_players.iterrows():
        p_team = normalize_team(str(row["team"]))
        payroll = team_payrolls.get(p_team, 0.0)
        v = calculate_player_valuation(
            row.to_dict(),
            team_payroll=payroll,
            cost_per_win=cost_per_win,
            salary_cap=salary_cap,
            metric_col=metric_col,
        )
        valuations.append(v.model_dump())

    df_board = pd.DataFrame(valuations).sort_values("net_surplus", ascending=False).reset_index(drop=True)
    return df_board
