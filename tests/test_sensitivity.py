"""Unit tests for parameter sensitivity analysis and rank elasticity."""

from boardman.sensitivity import analyze_trade_sensitivity, calculate_ranking_elasticity


def test_analyze_trade_sensitivity():
    """Verify that sensitivity grid calculates linear deltas and flips appropriately."""
    df_sens = analyze_trade_sensitivity(
        lambda_scales=[0.0, 0.5, 1.0],
        cost_per_win_range=[4_000_000.0, 5_229_872.0],
    )
    assert len(df_sens) == 6
    assert "delta_nsv" in df_sens.columns
    assert "verdict_flipped" in df_sens.columns

    # Pure linear (lambda_scale = 0.0) should have zero friction relief
    linear_rows = df_sens[df_sens["lambda_scale"] == 0.0]
    assert (linear_rows["friction_relief"] == 0.0).all()


def test_calculate_ranking_elasticity():
    """Verify ranking divergence between linear and apron-friction models."""
    df_rank = calculate_ranking_elasticity()
    assert len(df_rank) > 50
    assert "rank_shift" in df_rank.columns
    assert "friction_tax" in df_rank.columns

    # Heavily penalized Second Apron stars must show negative rank shift
    cle_stars = df_rank[df_rank["team"] == "CLE"]
    assert (cle_stars["friction_tax"] > 5_000_000.0).any()
