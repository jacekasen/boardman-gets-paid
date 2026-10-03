"""Unit tests for empirical lambda estimation from NBA salary dumps."""

from boardman.empirical_dumps import (
    EMPIRICAL_SALARY_DUMPS,
    estimate_revealed_preference_lambda,
)


def test_empirical_salary_dumps_structure():
    """Verify that empirical case studies contain validated financial figures."""
    assert len(EMPIRICAL_SALARY_DUMPS) >= 2
    denver_dump = EMPIRICAL_SALARY_DUMPS[0]
    assert denver_dump.salary_shed == 5_250_000.0
    assert denver_dump.estimated_pick_value == 8_000_000.0
    assert denver_dump.net_asset_cost_paid == 2_750_000.0
    assert denver_dump.implied_lambda_lower >= 0.40

    for dump in EMPIRICAL_SALARY_DUMPS:
        assert dump.salary_shed > 0
        assert dump.estimated_pick_value > 0
        assert dump.implied_lambda_lower > 0.0


def test_estimate_revealed_preference_lambda():
    """Verify that model's baseline lambda_3=0.70 is consistent with empirical lower bounds."""
    res = estimate_revealed_preference_lambda()

    assert res["is_baseline_consistent"] is True
    assert 0.40 <= res["implied_lambda_3_lower_bound"] <= 0.45
    assert res["cleveland_flip_break_even_lambda"] == 0.46
    assert res["model_baseline_lambda_3"] == 0.70
    assert "knife-edge" in res["headline_takeaway"]

