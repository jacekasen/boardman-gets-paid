"""Unit tests for empirical lambda estimation from NBA salary dumps."""

import pytest

from boardman.empirical_dumps import (
    EMPIRICAL_SALARY_DUMPS,
    calculate_luxury_tax,
    estimate_revealed_preference_lambda,
)


def test_empirical_salary_dumps_structure():
    """Verify that empirical case studies contain validated financial figures."""
    assert len(EMPIRICAL_SALARY_DUMPS) >= 2
    denver_dump = EMPIRICAL_SALARY_DUMPS[0]
    assert denver_dump.salary_shed == 5_250_000.0
    assert denver_dump.estimated_pick_value == 8_000_000.0
    assert denver_dump.net_asset_cost_paid == 2_750_000.0

    for dump in EMPIRICAL_SALARY_DUMPS:
        assert dump.salary_shed > 0
        assert dump.estimated_pick_value > 0
        assert dump.implied_lambda_lower >= 0.0


def test_calculate_luxury_tax():
    """Incremental tax brackets: $10M over at 2024-25 width (~$5.17M) charges 1.50x then 1.75x."""
    cap = 140_588_000.0
    width = 5_000_000.0 * cap / 136_021_000.0
    expected = width * 1.50 + (10_000_000.0 - width) * 1.75
    assert calculate_luxury_tax(180_000_000.0, 170_000_000.0, cap) == pytest.approx(expected)
    assert calculate_luxury_tax(160_000_000.0, 170_000_000.0, cap) == 0.0
    assert calculate_luxury_tax(180_000_000.0, 170_000_000.0, cap, repeater=True) > expected


def test_estimate_revealed_preference_lambda():
    """Once luxury tax savings are counted, the Denver dump does not bound lambda_3 above lambda_2."""
    res = estimate_revealed_preference_lambda(break_even_lambda_3=0.578)

    # Tax savings dwarf the net pick cost
    assert res["luxury_tax_saved_realized"] > 10_000_000.0
    assert res["luxury_tax_saved_decision_time"] >= res["luxury_tax_saved_realized"]
    assert res["net_cost_after_tax"] < 0

    # The tax-omitted bound reproduces the old (incorrect) 0.41 figure
    assert 0.40 <= res["implied_lambda_3_lower_bound_ignoring_tax"] <= 0.42
    assert res["implied_lambda_3_lower_bound"] < res["lambda_2"]
    assert res["implied_lambda_3_lower_bound_with_05_war"] < res["lambda_2"]
    assert res["is_bound_binding"] is False
    assert res["cleveland_flip_break_even_lambda"] == 0.578
    assert "non-binding" in res["headline_takeaway"]

