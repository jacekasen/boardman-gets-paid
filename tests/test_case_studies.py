from boardman.case_studies import (
    run_cleveland_dallas_strus_martin_escape,
    run_cleveland_detroit_apron_escape,
    run_cleveland_second_apron_trap,
    run_flagship_apron_escape_pair,
    run_kawhi_circumvention_case_study,
    run_spurs_celtics_liquidity_swap,
)


def test_cleveland_dallas_strus_martin_robust_flip():
    """Verify Flagship 1 (Robust Flip): Strus -> Martin flips from Linear Reject to Board Man Accept."""
    study = run_cleveland_dallas_strus_martin_escape()
    assert study["verdict_flipped"] is True
    assert study["linear_delta_a"] < 0, "Linear $/WAR model must reject the trade"
    assert study["boardman_delta_a"] > 0, "Apron friction model must accept the trade"
    assert study["friction_relief_a"] > 15_000_000.0, "Must unlock over $15M in roster-wide friction relief"
    assert study["break_even_lambda_3"] <= 0.36


def test_cleveland_detroit_high_stakes_assumption_dependent():
    """Verify Flagship 2 (High-Stakes Flip): Allen -> Stewart under war_projected requires high lambda_3."""
    # Under war_projected true talent, Stewart represents a severe 4.67 WAR drop
    study_projected = run_cleveland_detroit_apron_escape(metric_col="war_projected")
    assert study_projected["verdict_flipped"] is False
    assert study_projected["linear_delta_a"] < -15_000_000.0
    assert study_projected["break_even_lambda_3"] >= 0.75

    # Under single-season box scores (war_vorp), it flips because Allen missed games
    study_vorp = run_cleveland_detroit_apron_escape(metric_col="war_vorp")
    assert study_vorp["verdict_flipped"] is True
    assert study_vorp["boardman_delta_a"] > 0


def test_flagship_apron_escape_pair():
    """Verify that run_flagship_apron_escape_pair returns both cases side by side."""
    pair = run_flagship_apron_escape_pair()
    assert "robust_flip" in pair
    assert "high_stakes_flip" in pair
    assert pair["robust_flip"]["verdict_flipped"] is True
    assert pair["high_stakes_flip"]["verdict_flipped"] is False
    assert "takeaway" in pair


def test_cleveland_second_apron_case_study():
    """Verify Cleveland Second Apron trap case study remains illegal."""
    trade = run_cleveland_second_apron_trap()
    assert not trade.is_legal
    assert any("Second Apron aggregation violation" in v for v in trade.violations)


def test_spurs_celtics_liquidity_swap_case_study():
    """Verify Spurs-Celtics swap case study remains legal and net positive for SAS."""
    trade = run_spurs_celtics_liquidity_swap()
    assert trade.is_legal
    assert trade.delta_a.delta_nsv > 0


def test_kawhi_circumvention_case_study():
    """Verify Kawhi circumvention case study erosion equals off-cap cash."""
    study = run_kawhi_circumvention_case_study(off_cap_cash=10_000_000.0)
    assert study["surplus_erosion"] == 10_000_000.0
    assert study["circumvented_nsv"] == study["official_nsv"] - 10_000_000.0
