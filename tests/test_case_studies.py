"""Unit tests for pre-packaged benchmark case studies."""

from boardman.case_studies import (
    run_cleveland_second_apron_trap,
    run_kawhi_circumvention_case_study,
    run_spurs_celtics_liquidity_swap,
)


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
