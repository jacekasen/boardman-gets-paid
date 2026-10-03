from boardman.case_studies import (
    run_cleveland_detroit_apron_escape,
    run_cleveland_second_apron_trap,
    run_kawhi_circumvention_case_study,
    run_spurs_celtics_liquidity_swap,
)


def test_cleveland_detroit_apron_escape_thesis_flip():
    """Verify that Apron Friction flips the decision from Linear Reject to Board Man Accept."""
    study = run_cleveland_detroit_apron_escape()
    assert study["verdict_flipped"] is True
    assert study["linear_delta_a"] < 0, "Linear $/WAR model must reject the trade"
    assert study["boardman_delta_a"] > 0, "Apron friction model must accept the trade"
    assert study["friction_relief_a"] > 15_000_000.0, "Must unlock over $15M in roster-wide friction relief"


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
