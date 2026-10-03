"""Unit tests for parameter sensitivity analysis, break-even frontier, and rank elasticity."""

import numpy as np

from boardman.sensitivity import (
    analyze_trade_sensitivity,
    calculate_apron_escape_frontier,
    calculate_break_even_lambda_3,
    calculate_flagship_uncertainty_pair,
    calculate_headline_uncertainty,
    calculate_ranking_elasticity,
    scan_apron_escape_trades,
)



def test_analyze_trade_sensitivity():
    """Verify that sensitivity grid calculates linear deltas and flips appropriately."""
    df_sens = analyze_trade_sensitivity(
        lambda_scales=[0.0, 0.5, 1.0, 2.0],
        cost_per_win_range=[5_229_872.0, 6_000_000.0],
    )
    assert len(df_sens) == 8
    assert "delta_nsv" in df_sens.columns
    assert "linear_delta" in df_sens.columns
    assert "verdict_flipped" in df_sens.columns

    # 1. At lambda_scale = 0.0, delta_nsv MUST strictly equal linear_delta (pure $/WAR model)
    zero_rows = df_sens[df_sens["lambda_scale"] == 0.0]
    for _, row in zero_rows.iterrows():
        assert np.isclose(row["delta_nsv"], row["linear_delta"], atol=1.0)
        assert row["delta_nsv"] < 0, "Pure linear $/WAR must reject the talent-sacrifice trade!"
        assert row["verdict_flipped"] is False

    # 2. At lambda_scale >= 1.0, delta_nsv MUST be positive for Cleveland escaping 2nd apron
    one_rows = df_sens[df_sens["lambda_scale"] >= 1.0]
    assert (one_rows["delta_nsv"] > 0).all()
    assert (one_rows["verdict_flipped"] == True).all()

    # 3. Monotonic growth with respect to lambda scale
    subset = df_sens[df_sens["cost_per_win_m"] == 5.23].sort_values("lambda_scale")
    nsv_vals = subset["delta_nsv"].tolist()
    assert nsv_vals == sorted(nsv_vals), "Delta NSV must increase monotonically with lambda scale!"


def test_calculate_apron_escape_frontier():
    """Verify the break-even allowable talent loss expansion curve."""
    df_frontier = calculate_apron_escape_frontier(
        team="CLE",
        salary_shed_steps=[5_000_000.0],
    )
    assert len(df_frontier) == 1
    row = df_frontier.iloc[0]
    # Under linear: allowable WAR loss is -0.96 WAR
    assert np.isclose(row["max_war_loss_linear"], -0.96, atol=0.05)
    # Under apron: allowable WAR loss expands to ~ -3.93 WAR
    assert row["max_war_loss_apron"] < -3.5
    assert row["expansion_factor"] > 3.5


def test_scan_apron_escape_trades():
    """Verify that multiple legal trades flip across the league beyond a single anecdote."""
    df_flips = scan_apron_escape_trades(team="CLE")
    # Must find multiple trades across diverse partner franchises
    assert len(df_flips) >= 15
    # Franchise cornerstones are protected from the outgoing pool by default
    assert not df_flips["target_player"].isin(["Donovan Mitchell", "Evan Mobley", "James Harden"]).any()
    assert (df_flips["linear_delta"] < 0).all()
    assert (df_flips["boardman_delta"] > 0).all()
    # Check that partner teams include multiple franchises
    unique_partners = df_flips["partner_team"].unique()
    assert len(unique_partners) >= 3


def test_calculate_ranking_elasticity():
    """Verify ranking divergence between linear and apron-friction models."""
    df_rank = calculate_ranking_elasticity()
    assert len(df_rank) > 50
    assert "rank_shift" in df_rank.columns
    assert "friction_tax" in df_rank.columns

    # Heavily penalized Second Apron stars must show negative rank shift
    cle_stars = df_rank[df_rank["team"] == "CLE"]
    assert (cle_stars["friction_tax"] > 5_000_000.0).any()


def test_calculate_headline_uncertainty():
    """Verify Monte Carlo simulation metrics for the headline Cleveland escape using sourced cost components."""
    # Robust flip (Strus -> Martin) under war_projected
    res = calculate_headline_uncertainty(n_trials=2000, seed=42)
    assert res["win_probability"] == 1.0
    assert res["mean_delta_nsv"] > 10_000_000.0
    assert len(res["scenario_interval_90"]) == 2
    assert res["scenario_interval_90"][0] > 0
    assert "Cleveland" in res["headline_takeaway"]
    assert np.isclose(res["break_even_lambda_3"], calculate_break_even_lambda_3()["break_even_lambda_3"], atol=0.005)

    # High-stakes flip (Allen -> Stewart) under war_projected
    res_high = calculate_headline_uncertainty(
        send_a=["Jarrett Allen"], team_b="DET", send_b=["Isaiah Stewart"], n_trials=2000, seed=42
    )
    assert 0.01 <= res_high["win_probability"] <= 0.08
    assert res_high["mean_delta_nsv"] < 0
    assert res_high["scenario_interval_90"][0] < 0


def test_calculate_break_even_lambda_3():
    """Break-even lambda_3 (lambda_2 held fixed) is computed live and zeroes Delta NSV."""
    res = calculate_break_even_lambda_3()
    assert 0.35 <= res["break_even_lambda_3"] <= 0.38
    assert res["lambda_2_held_fixed"] == 0.35
    # Required relief is exactly the linear $/WAR deficit
    assert np.isclose(res["required_friction_relief"], -res["linear_delta"])
    assert res["baseline_friction_relief"] > res["required_friction_relief"]
    # Baseline Delta NSV equals slope * (baseline - break-even)
    implied = res["delta_nsv_per_unit_lambda_3"] * (res["baseline_lambda_3"] - res["break_even_lambda_3"])
    assert np.isclose(implied, res["baseline_delta_nsv"], rtol=0.01)


def test_calculate_flagship_uncertainty_pair():
    """Verify that calculate_flagship_uncertainty_pair computes both trades."""
    pair = calculate_flagship_uncertainty_pair(n_trials=2000, seed=42)
    assert pair["robust_flip"]["win_probability"] == 1.0
    assert pair["high_stakes_flip"]["win_probability"] < 0.10
    assert "Robust Flip" in pair["takeaway"]



