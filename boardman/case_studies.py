"""Benchmark case studies: Real-world CBA scenarios, apron traps, and the Kawhi circumvention trade."""

from __future__ import annotations

from typing import Any

import pandas as pd

from boardman.config import MASTER_PLAYERS_PARQUET, MASTER_TEAMS_PARQUET
from boardman.trade_engine import TradeEvaluation, evaluate_trade
from boardman.valuation import DEFAULT_COST_PER_WIN, calculate_player_valuation


def run_cleveland_detroit_apron_escape(
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    metric_col: str = "war_vorp",
) -> dict[str, Any]:
    """Flagship Case Study: The Apron Threshold Flip.

    Cleveland ($211.7M payroll, Bracket 3 / Second Apron) trades Jarrett Allen ($20.0M)
    to Detroit for Isaiah Stewart ($15.0M).

    Mathematical Thesis:
    - Linear $/WAR Model: Cleveland gives up on-court WAR to save only $5M in salary.
      Linear Delta = (Salary Out - Salary In) + (WAR Delta * Cost-Per-Win).
      Linear Verdict: REJECT (Fleeced by -$10.53M).
    - Board Man Apron Model: Shedding $5M drops Cleveland to $206.7M, breaking through the
      Second Apron ($207.8M) into Bracket 2! Total roster friction drops from $31.07M to $15.14M,
      unlocking +$15.93M in roster-wide friction relief.
      Net Surplus Delta = Linear Delta + Friction Relief = +$5.40M.
      Board Man Verdict: ACCEPT (Cleveland gains +$5.40M in net franchise flexibility).
    """
    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    trade = evaluate_trade(
        team_a="CLE",
        send_a=["Jarrett Allen"],
        team_b="DET",
        send_b=["Isaiah Stewart"],
        df_players=df_players,
        df_teams=df_teams,
        cost_per_win=cost_per_win,
        metric_col=metric_col,
    )

    # Dynamically extract player WAR values from dataset
    allen_row = df_players[(df_players["team"] == "CLE") & (df_players["player_name"] == "Jarrett Allen")]
    stewart_row = df_players[(df_players["team"] == "DET") & (df_players["player_name"] == "Isaiah Stewart")]

    war_out = float(allen_row[metric_col].iloc[0]) if not allen_row.empty else 4.86
    war_in = float(stewart_row[metric_col].iloc[0]) if not stewart_row.empty else 1.89

    war_delta = war_in - war_out  # negative (lost production)
    salary_saved = trade.salary_out_a - trade.salary_in_a  # +$5.0M
    linear_delta = salary_saved + (war_delta * cost_per_win)

    return {
        "trade": trade,
        "team_a": "CLE",
        "team_b": "DET",
        "war_out": war_out,
        "war_in": war_in,
        "war_delta": round(war_delta, 2),
        "salary_saved": round(salary_saved, 2),
        "linear_delta_a": round(linear_delta, 2),
        "linear_verdict_a": f"REJECT (Loss of ${abs(linear_delta)/1e6:.2f}M in linear on-court value)",
        "friction_relief_a": round(trade.delta_a.friction_relief, 2),
        "boardman_delta_a": round(trade.delta_a.delta_nsv, 2),
        "boardman_verdict_a": f"ACCEPT (Gain of +${trade.delta_a.delta_nsv/1e6:.2f}M in net roster surplus & apron escape)",
        "verdict_flipped": bool((linear_delta < 0) and (trade.delta_a.delta_nsv > 0)),
        "bracket_transition": trade.delta_a.bracket_transition,
    }


def run_cleveland_second_apron_trap() -> TradeEvaluation:
    """Case Study: Cleveland Cavaliers trapped in the Second Apron.

    Cleveland ($211.7M payroll, Bracket 3, lambda = 0.70) attempts to combine
    Max Strus ($15.9M) and Dennis Schröder ($14.1M) to acquire Derrick White ($28.1M).

    Demonstrates:
    - Automatic rejection under the 2023 CBA zero salary aggregation rule.
    """
    return evaluate_trade(
        team_a="CLE",
        send_a=["Max Strus", "Dennis Schröder"],
        team_b="BOS",
        send_b=["Derrick White"],
    )


def run_spurs_celtics_liquidity_swap() -> TradeEvaluation:
    """Case Study: Flexible rebuilder (SAS) absorbing a prime star (BOS).

    San Antonio (Bracket 0, lambda = 0.00) sends Harrison Barnes ($19.0M)
    and Kelly Olynyk ($13.4M) to Boston for Derrick White ($28.1M).

    Demonstrates:
    - High positive Net Surplus swing (+~$36.8M) for SAS by leveraging sub-tax cap room.
    """
    return evaluate_trade(
        team_a="SAS",
        send_a=["Harrison Barnes", "Kelly Olynyk"],
        team_b="BOS",
        send_b=["Derrick White"],
    )


def run_kawhi_circumvention_case_study(
    off_cap_cash: float = 7_000_000.0,
    audit_probability: float = 0.30,
) -> dict[str, Any]:
    """Case Study: The 'Board Man Gets Paid' Cap Circumvention Analysis & Penalty Calculus.

    Evaluates Kawhi Leonard's asset value and the risk-adjusted expected penalty to ownership:
    - Statutory on-the-books salary ($50.0M).
    - Shadow off-the-cap sponsor contracts ($7.0M/yr via Aspiration).
    - Risk-adjusted expected penalty:
        E[Penalty] = P(audit) * [Statutory Cash Fine ($30M) + 5 First-Round Picks ($57.5M assumed draft equity)]
      *Note:* The 30% audit probability and $11.5M/pick are exploratory parameter assumptions
      to illustrate risk-adjusted decision math, inspired by reporting from Pablo Torre and
      the NBA's retention of Wachtell Lipton.

    Sources:
    - Pablo Torre, 'Pablo Torre Finds Out' (Meadowlark Media, investigative reporting).
    - Wachtell, Lipton, Rosen & Katz (Independent Counsel retained by NBA Board of Governors).
    - NBA Constitution Article 35 & 2023 CBA Article XIII.
    """
    kawhi_data = {
        "player_id": "leonaka01",
        "player_name": "Kawhi Leonard",
        "team": "LAC",
        "salary": 50_000_000.0,
        "cap_share": 32.33,
        "war_vorp": 14.31,
    }
    lac_payroll = 188_928_780.0  # LAC in Bracket 1 (Tax, lambda = 0.15)

    val_official = calculate_player_valuation(kawhi_data, team_payroll=lac_payroll, uncle_dennis_cash=0.0)
    val_circumvented = calculate_player_valuation(
        kawhi_data, team_payroll=lac_payroll, uncle_dennis_cash=off_cap_cash
    )

    # Risk-adjusted penalty calculus:
    # 5 First round picks * assumed $11.5M rookie surplus curve = $57.5M draft capital loss
    # $30M cash fine
    total_statutory_penalty = 30_000_000.0 + 57_500_000.0
    expected_penalty_cost = audit_probability * total_statutory_penalty

    return {
        "player": "Kawhi Leonard",
        "official_salary": 50_000_000.0,
        "off_cap_endorsement": off_cap_cash,
        "audit_probability": audit_probability,
        "war": 14.31,
        "fair_value": val_official.fair_value,
        "official_nsv": val_official.net_surplus,
        "circumvented_nsv": val_circumvented.net_surplus,
        "surplus_erosion": val_official.net_surplus - val_circumvented.net_surplus,
        "expected_penalty_cost": round(expected_penalty_cost, 2),
        "total_penalty_if_caught": total_statutory_penalty,
        "citations": [
            "Pablo Torre Finds Out (Meadowlark Media, investigative reporting on Aspiration sponsorship)",
            "Wachtell, Lipton, Rosen & Katz (Retained independent counsel for NBA Board of Governors)",
            "NBA Constitution Article 35 & 2023 CBA Article XIII (Salary Cap Circumvention & Unauthorized Agreements)",
        ],
    }
