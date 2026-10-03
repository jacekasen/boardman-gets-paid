"""Benchmark case studies: Real-world CBA scenarios, apron traps, and the Kawhi circumvention trade."""

from __future__ import annotations

import pandas as pd

from boardman.trade_engine import TradeEvaluation, evaluate_trade
from boardman.valuation import calculate_player_valuation


def run_cleveland_second_apron_trap() -> TradeEvaluation:
    """Case Study 1: Cleveland Cavaliers trapped in the Second Apron.

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
    """Case Study 2: Flexible rebuilder (SAS) absorbing a prime star (BOS).

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


def run_kawhi_circumvention_case_study(off_cap_cash: float = 7_000_000.0) -> dict[str, Any]:
    """Case Study 3: The 'Board Man Gets Paid' Cap Circumvention Analysis.

    Evaluates Kawhi Leonard's asset value under:
    1. Statutory Official Cap Sheet ($50.0M cap hit).
    2. Real Economic Cost factoring in $7.0M/yr in off-the-cap sponsor payments (Aspiration).
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

    return {
        "player": "Kawhi Leonard",
        "official_salary": 50_000_000.0,
        "off_cap_endorsement": off_cap_cash,
        "war": 14.31,
        "fair_value": val_official.fair_value,
        "official_nsv": val_official.net_surplus,
        "circumvented_nsv": val_circumvented.net_surplus,
        "surplus_erosion": val_official.net_surplus - val_circumvented.net_surplus,
    }
