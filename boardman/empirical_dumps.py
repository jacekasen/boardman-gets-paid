"""Empirical calibration of apron friction penalty (lambda) from revealed-preference salary dumps.

Validates the model's hypothesized lambda parameter against actual transaction prices
paid by NBA franchises (specifically Denver dumping Reggie Jackson in June 2024)
to escape Second Apron operational restrictions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from boardman.config import (
    FRICTION_LAMBDA,
    SALARY_CAP_2023_24_BASE,
    SOURCE_PLAYER_SALARIES,
    SOURCE_TEAM_SALARIES,
)
from boardman.clustering import HISTORICAL_CBA_THRESHOLDS
from boardman.valuation import DEFAULT_COST_PER_WIN

# 2024-25 statutory thresholds used for the Denver benchmark
SALARY_CAP_2024_25 = 140_588_000.0
LUXURY_TAX_2024_25 = HISTORICAL_CBA_THRESHOLDS["2024-25"]["tax"]
SECOND_APRON_2024_25 = HISTORICAL_CBA_THRESHOLDS["2024-25"]["apron2"]

# 2023 CBA Art. VII Sec. 12: incremental luxury tax rates per tax bracket. Rates above the last listed
# bracket keep rising by $0.50 per bracket. Bracket width ($5M in 2023-24) is indexed to cap growth.
NON_REPEATER_TAX_RATES = [1.50, 1.75, 2.50, 3.25]
REPEATER_TAX_RATES = [2.50, 2.75, 3.50, 4.25]
TAX_BRACKET_WIDTH_2023_24 = 5_000_000.0


def calculate_luxury_tax(
    payroll: float,
    tax_line: float,
    salary_cap: float,
    repeater: bool = False,
) -> float:
    """Luxury tax owed on a payroll under the 2023 CBA incremental bracket schedule."""
    excess = payroll - tax_line
    if excess <= 0:
        return 0.0
    width = TAX_BRACKET_WIDTH_2023_24 * salary_cap / SALARY_CAP_2023_24_BASE
    rates = REPEATER_TAX_RATES if repeater else NON_REPEATER_TAX_RATES
    tax = 0.0
    bracket = 0
    while excess > 0:
        rate = rates[bracket] if bracket < len(rates) else rates[-1] + 0.50 * (bracket - len(rates) + 1)
        chunk = min(excess, width)
        tax += chunk * rate
        excess -= chunk
        bracket += 1
    return tax


class SalaryDumpCaseStudy(BaseModel):
    """Documented NBA transaction where a contender sacrificed draft equity to shed salary."""

    team: str = Field(description="Franchise dumping salary")
    season: str = Field(description="Transaction season")
    player_shed: str = Field(description="Player contract dumped")
    salary_shed: float = Field(description="Annual salary shed in USD (counts as benefit/savings)")
    draft_equity_attached: str = Field(description="Draft picks attached to incentivize trade partner")
    estimated_pick_value: float = Field(description="Estimated economic net present value of attached picks in USD (cost paid)")
    net_asset_cost_paid: float = Field(description="Net economic cost paid: pick equity minus salary saved in USD")
    target_threshold: str = Field(description="Target CBA threshold avoided or escaped")
    implied_lambda_lower: float = Field(description="Derived empirical lower bound on lambda")
    rationale: str = Field(description="Front-office strategic context")


EMPIRICAL_SALARY_DUMPS: list[SalaryDumpCaseStudy] = [
    SalaryDumpCaseStudy(
        team="DEN",
        season="2024-25",
        player_shed="Reggie Jackson",
        salary_shed=5_250_000.0,
        draft_equity_attached="3 Second-Round Picks (2025, 2029, 2030)",
        estimated_pick_value=8_000_000.0,  # ~ $2.67M per mid/high 2nd round pick in surplus equity
        net_asset_cost_paid=2_750_000.0,  # $8.0M pick equity sacrificed minus $5.25M salary saved (before tax)
        target_threshold="Second Apron ($188.93M in 2024-25)",
        implied_lambda_lower=0.0,  # Non-binding once luxury tax savings are counted (see estimate_revealed_preference_lambda)
        rationale=(
            "At the June 27, 2024 decision time, pre-free agency projections positioned Denver at ~$193.0M "
            "(~$4.1M over the 2024-25 Second Apron of $188.93M, assuming Kentavious Caldwell-Pope re-signed). "
            "By attaching three 2nd-round draft picks to dump Reggie Jackson's $5.25M player option to Charlotte "
            "for zero return salary, Denver preemptively shed salary (and subsequently KCP departed in free agency, "
            "leaving realized payroll at $182.57M, or $187.82M with Jackson, $1.1M below the apron). Net of salary saved, "
            "the picks cost $2.75M, but Denver was deep in the luxury tax, saving roughly $14M-$19M in tax. Tax savings "
            "alone justify the trade, so this transaction does not bound lambda_3 above lambda_2."
        ),
    ),
    SalaryDumpCaseStudy(
        team="DAL",
        season="2024-25",
        player_shed="Tim Hardaway Jr.",
        salary_shed=11_890_000.0,  # $16.19M outgoing - $4.30M Quentin Grimes incoming
        draft_equity_attached="3 Second-Round Picks",
        estimated_pick_value=8_000_000.0,
        net_asset_cost_paid=-3_890_000.0,  # Dallas saved $11.89M salary against $8M pick equity
        target_threshold="First Apron Hard Cap ($178.13M in 2024-25)",
        implied_lambda_lower=0.35,
        rationale=(
            "Dallas attached 3 second-round picks to clear $11.89M in cap room, creating the operational "
            "slack needed to execute the Klay Thompson sign-and-trade while strictly remaining below "
            "the First Apron hard-cap ceiling. Note: This transaction is an illustrative First Apron "
            "hard-cap precedent and does not inform the Second Apron (lambda_3) parameter."
        ),
    ),
]


def estimate_revealed_preference_lambda(
    salaries_path: Path = SOURCE_PLAYER_SALARIES,
    team_salaries_path: Path = SOURCE_TEAM_SALARIES,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    break_even_lambda_3: float | None = None,
) -> dict[str, Any]:
    """Revealed-preference lower bound on lambda_3 from Denver's Reggie Jackson dump, including tax savings.

    Mathematical Formulation:
    -------------------------
    When a franchise sacrifices pick equity E to dump salary S with zero incoming salary, it saves S in
    salary and T_tax in luxury tax, and gives up E plus any on-court production (Delta_W * C_w).
    The trade is rational if and only if:
        Delta_Friction + S + T_tax >= E + (Delta_W * C_w)

    With Delta_Friction = lambda_3 * B_pre - lambda_2 * B_post (Bracket 3 -> Bracket 2):
        lambda_3 >= (E - S - T_tax + Delta_W * C_w + lambda_2 * B_post) / B_pre

    T_tax is computed from the 2023 CBA incremental tax schedule (non-repeater rates, which give the
    smallest savings and therefore the most favorable bound for the model). Two payroll baselines:
      - Decision-time: projected payroll at the June 2024 dump (~$4.07M over the Second Apron).
      - Realized: Denver's end-of-season 2024-25 payroll plus Jackson's salary (smaller tax savings,
        since Denver later shed more salary). This is the conservative case reported as the headline.

    A lower bound at or below lambda_2 is non-binding: the model already requires lambda_3 >= lambda_2.
    """
    rj_sal = 5_250_000.0
    pick_equity = 8_000_000.0
    salary_saved = rj_sal
    net_cost_before_tax = pick_equity - salary_saved  # $2,750,000

    # Denver 2024-25 roster quadratic bases (fallbacks match the dataset when the source is unavailable)
    b_pre = 42_249_621.37
    b_post = 42_053_569.79
    realized_payroll_post = 182_574_315.0

    if salaries_path.exists():
        try:
            df_sal = pd.read_csv(salaries_path)
            den = df_sal[(df_sal["team"] == "DEN") & (df_sal["season"] == "2024-25")].dropna(subset=["salary"])
            if not den.empty:
                rj_row = pd.DataFrame([{"salary": rj_sal}])
                den_pre = pd.concat([den[["salary"]], rj_row], ignore_index=True)
                b_pre = float(sum((s**2) / SALARY_CAP_2024_25 for s in den_pre["salary"]))
                b_post = float(sum((s**2) / SALARY_CAP_2024_25 for s in den["salary"]))
        except Exception:
            pass

    if team_salaries_path.exists():
        try:
            df_team = pd.read_csv(team_salaries_path)
            row = df_team[(df_team["team"] == "DEN") & (df_team["season"] == "2024-25")]
            if not row.empty:
                realized_payroll_post = float(row["team_known_salary_total"].iloc[0])
        except Exception:
            pass

    def tax_saved(payroll_pre: float) -> float:
        return calculate_luxury_tax(payroll_pre, LUXURY_TAX_2024_25, SALARY_CAP_2024_25) - calculate_luxury_tax(
            payroll_pre - rj_sal, LUXURY_TAX_2024_25, SALARY_CAP_2024_25
        )

    decision_payroll_pre = SECOND_APRON_2024_25 + 4_070_000.0
    realized_payroll_pre = realized_payroll_post + rj_sal
    tax_saved_decision = tax_saved(decision_payroll_pre)
    tax_saved_realized = tax_saved(realized_payroll_pre)

    lambda_2 = FRICTION_LAMBDA[2]

    def bound(tax: float, war_loss: float) -> float:
        return (net_cost_before_tax - tax + war_loss * cost_per_win + lambda_2 * b_post) / b_pre

    # Headline: conservative (realized payroll, smallest tax savings)
    lower_0_war = bound(tax_saved_realized, 0.0)
    lower_half_war = bound(tax_saved_realized, 0.5)
    lower_decision = bound(tax_saved_decision, 0.0)
    # The bound omitting tax, kept only to show how much the omitted term mattered
    lower_no_tax = bound(0.0, 0.0)

    is_binding = lower_half_war > lambda_2

    if break_even_lambda_3 is None:
        from boardman.sensitivity import calculate_break_even_lambda_3

        break_even_lambda_3 = calculate_break_even_lambda_3()["break_even_lambda_3"]

    return {
        "benchmark_transaction": "Denver Nuggets -> Charlotte Hornets (Reggie Jackson + 3 SRPs, June 2024)",
        "salary_shed": salary_saved,
        "draft_equity_sacrificed": pick_equity,
        "net_asset_cost_paid": net_cost_before_tax,
        "luxury_tax_saved_realized": round(tax_saved_realized, 2),
        "luxury_tax_saved_decision_time": round(tax_saved_decision, 2),
        "net_cost_after_tax": round(net_cost_before_tax - tax_saved_realized, 2),
        "denver_roster_base_pre": round(b_pre, 2),
        "denver_roster_base_post": round(b_post, 2),
        "implied_lambda_3_lower_bound": round(lower_0_war, 3),
        "implied_lambda_3_lower_bound_with_05_war": round(lower_half_war, 3),
        "implied_lambda_3_lower_bound_decision_time": round(lower_decision, 3),
        "implied_lambda_3_lower_bound_ignoring_tax": round(lower_no_tax, 3),
        "lambda_2": lambda_2,
        "is_bound_binding": bool(is_binding),
        "model_baseline_lambda_3": FRICTION_LAMBDA[3],
        "cleveland_flip_break_even_lambda": break_even_lambda_3,
        "headline_takeaway": (
            f"Counting luxury tax, Denver's dump saved ~${tax_saved_realized / 1e6:.1f}M in tax against a "
            f"${net_cost_before_tax / 1e6:.2f}M net pick cost, so tax savings alone justify it. The implied bound "
            f"(lambda_3 >= {lower_0_war:.2f}, or {lower_half_war:.2f} with a 0.5 WAR loss) sits below "
            f"lambda_2 = {lambda_2:.2f} and is non-binding. Salary-dump data does not identify lambda_3; "
            f"Cleveland's break-even (lambda_3 >= {break_even_lambda_3:.2f}) must be judged against the "
            "cost-breakdown estimate instead."
        ),
        "case_studies": [c.model_dump() for c in EMPIRICAL_SALARY_DUMPS],
    }
