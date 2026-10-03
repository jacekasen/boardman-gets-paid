"""Core valuation engine: Fair Production Value, Gross Surplus, Apron Friction Tax, and Net Surplus Value."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from boardman.config import (
    DEFAULT_METRIC,
    DEFAULT_SEASON,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    MINIMUM_SALARY_2025_26,
    SALARY_CAP_2025_26,
    get_team_bracket,
    normalize_team,
)

# Calibrated 2025-26 marginal $/WAR from calibrate_cost_per_win() on the processed player table.
# Recorded in ingestion_report.json; tests assert the two stay in sync.
DEFAULT_COST_PER_WIN = 5_421_253.62
REPLACEMENT_SALARY = MINIMUM_SALARY_2025_26
VETERAN_CALIBRATION_FLOOR = 5_000_000


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
    gross_surplus: float | None = Field(description="Fair value minus cap hit; None when salary is unverified")
    bracket: int
    lambda_tax: float
    friction_tax: float
    net_surplus: float | None = Field(description="Gross surplus minus friction; None when salary is unverified")
    surplus_efficiency: float | None = Field(description="Net Surplus per dollar of cap hit (NSV / Salary)")
    is_dead_money: bool = False
    is_salary_known: bool = True
    contract_tier: str = "Standard"
    roi_multiple: float | None = Field(default=None, description="Fair Production Value divided by Salary (e.g. 2.5x)")
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


def calibrate_cost_per_win(
    df_players: pd.DataFrame,
    metric_col: str = DEFAULT_METRIC,
    replacement_salary: float = REPLACEMENT_SALARY,
    veteran_floor: float = VETERAN_CALIBRATION_FLOOR,
) -> float:
    """Marginal open-market price of one win above replacement.

    C_w = sum(cap hit - replacement salary) / sum(WAR) over every active, verified veteran
    contract at or above the floor. Outcomes are not filtered, so contracts that produced
    little or negative WAR stay in the market price.
    """
    vets = df_players[
        (df_players["salary"] >= veteran_floor)
        & (~df_players["is_dead_money"].astype(bool))
        & (df_players["is_salary_known"].astype(bool))
    ]
    wins = float(vets[metric_col].sum())
    if wins <= 0:
        raise ValueError("Veteran calibration pool has non-positive total WAR")
    return float((vets["salary"] - replacement_salary).sum() / wins)


def compute_apron_friction(
    cap_hit: float,
    team_payroll: float,
    salary_cap: float = SALARY_CAP_2025_26,
    friction_lambda: dict[int, float] | None = None,
) -> tuple[int, float, float]:
    """Calculate the Apron Friction Tax for a contract given the team's payroll and bracket.

    Returns:
        tuple of (bracket: int, lambda_tax: float, friction_tax: float)
    """
    if cap_hit <= 0:
        bracket, lambda_tax = get_team_bracket(team_payroll, friction_lambda=friction_lambda)
        return bracket, lambda_tax, 0.0

    bracket, lambda_tax = get_team_bracket(team_payroll, friction_lambda=friction_lambda)
    # Quadratic drag: lambda * cap_hit * (cap_hit / salary_cap)
    friction = lambda_tax * cap_hit * (cap_hit / salary_cap)
    return bracket, lambda_tax, friction


def calculate_player_valuation(
    player: dict[str, Any] | BaseModel,
    team_payroll: float,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = DEFAULT_METRIC,
    uncle_dennis_cash: float = 0.0,
    friction_lambda: dict[int, float] | None = None,
    replacement_salary: float = REPLACEMENT_SALARY,
) -> PlayerValuation:
    """Evaluate an individual player's Fair Production Value, GSV, Friction Tax, and NSV.

    A replacement-level (0 WAR) player is worth the league minimum, so
    FV = replacement_salary + WAR * C_w. Surplus is left as None when the salary is unverified.
    """
    data = player.model_dump() if isinstance(player, BaseModel) else dict(player)

    player_id = str(data.get("player_id", "unknown"))
    player_name = str(data.get("player_name", "Unknown Player"))
    team = normalize_team(str(data.get("team", "FA")))
    cap_hit = float(data.get("salary", 0.0))
    cap_share = float(data.get("cap_share", (cap_hit / salary_cap) * 100.0 if salary_cap > 0 else 0.0))
    is_dead_money = bool(data.get("is_dead_money", False))
    is_salary_known = bool(data.get("is_salary_known", cap_hit > 0))
    contract_tier = str(data.get("contract_tier", "Standard"))

    war = float(data.get(metric_col, data.get("war_projected", data.get("war_vorp", data.get("war", 0.0)))))
    effective_cost = cap_hit + uncle_dennis_cash

    bracket, lambda_tax = get_team_bracket(team_payroll, friction_lambda=friction_lambda)

    if is_dead_money:
        war = 0.0
        fair_value = 0.0
        gross_surplus = -effective_cost
        friction_tax = 0.0
        net_surplus = gross_surplus
        surplus_efficiency = -1.0 if cap_hit > 0 else 0.0
        roi_multiple = 0.0
    elif not is_salary_known or cap_hit <= 0:
        fair_value = replacement_salary + war * cost_per_win
        gross_surplus = None
        friction_tax = 0.0
        net_surplus = None
        surplus_efficiency = None
        roi_multiple = None
    else:
        fair_value = replacement_salary + war * cost_per_win
        gross_surplus = fair_value - effective_cost
        _, _, friction_tax = compute_apron_friction(
            cap_hit, team_payroll, salary_cap=salary_cap, friction_lambda=friction_lambda
        )
        net_surplus = gross_surplus - friction_tax
        surplus_efficiency = net_surplus / cap_hit
        roi_multiple = round(fair_value / cap_hit, 2)

    return PlayerValuation(
        player_id=player_id,
        player_name=player_name,
        team=team,
        salary=cap_hit,
        cap_share=cap_share,
        war=round(war, 2),
        cost_per_win=cost_per_win,
        fair_value=round(fair_value, 2),
        gross_surplus=None if gross_surplus is None else round(gross_surplus, 2),
        bracket=bracket,
        lambda_tax=lambda_tax,
        friction_tax=round(friction_tax, 2),
        net_surplus=None if net_surplus is None else round(net_surplus, 2),
        surplus_efficiency=None if surplus_efficiency is None else round(surplus_efficiency, 3),
        is_dead_money=is_dead_money,
        is_salary_known=is_salary_known,
        contract_tier=contract_tier,
        roi_multiple=roi_multiple,
        uncle_dennis_cash=round(uncle_dennis_cash, 2),
    )


def calculate_roster_valuation(
    players: list[dict[str, Any] | BaseModel],
    team_payroll: float | None = None,
    team_code: str = "TEAM",
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = DEFAULT_METRIC,
    friction_lambda: dict[int, float] | None = None,
) -> TeamValuation:
    """Aggregate fair values, gross surplus, friction penalties, and net surplus across a full roster."""
    player_dicts = [p.model_dump() if isinstance(p, BaseModel) else dict(p) for p in players]

    # If team_payroll is omitted, compute sum of player cap hits
    if team_payroll is None:
        team_payroll = sum(float(p.get("salary", 0.0)) for p in player_dicts)

    bracket, lambda_tax = get_team_bracket(team_payroll, friction_lambda=friction_lambda)

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
            friction_lambda=friction_lambda,
        )
        valuations.append(val)
        total_fv += val.fair_value
        total_gsv += val.gross_surplus or 0.0
        total_friction += val.friction_tax
        total_nsv += val.net_surplus or 0.0

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
    metric_col: str = DEFAULT_METRIC,
    friction_lambda: dict[int, float] | None = None,
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
        friction_lambda=friction_lambda,
    )

    post_val = calculate_roster_valuation(
        post_roster,
        team_payroll=post_payroll,
        team_code=team_code,
        cost_per_win=cost_per_win,
        salary_cap=salary_cap,
        metric_col=metric_col,
        friction_lambda=friction_lambda,
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
    metric_col: str = DEFAULT_METRIC,
    cost_per_win: float | None = None,
    salary_cap: float = SALARY_CAP_2025_26,
    friction_lambda: dict[int, float] | None = None,
) -> pd.DataFrame:
    """Build full league leaderboard of player valuations, Gross Surplus, Friction, and Net Surplus.

    When cost_per_win is omitted it is calibrated from df_players on the same metric being valued.
    Players with unverified salaries have no surplus and sort to the bottom.
    """
    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)
    if cost_per_win is None:
        cost_per_win = calibrate_cost_per_win(df_players, metric_col=metric_col)

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
            friction_lambda=friction_lambda,
        )
        valuations.append(v.model_dump())

    df_board = pd.DataFrame(valuations).sort_values("net_surplus", ascending=False, na_position="last").reset_index(drop=True)
    return df_board
