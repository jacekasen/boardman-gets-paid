"""Unit tests for empirical lambda estimation from NBA salary dumps."""

from boardman.empirical_dumps import (
    EMPIRICAL_SALARY_DUMPS,
    estimate_revealed_preference_lambda,
)


def test_empirical_salary_dumps_structure():
    """Verify that empirical case studies contain validated financial figures."""
    assert len(EMPIRICAL_SALARY_DUMPS) >= 2
    for dump in EMPIRICAL_SALARY_DUMPS:
        assert dump.salary_shed > 0
        assert dump.estimated_pick_value > 0
        assert dump.total_willingness_to_pay == dump.salary_shed + dump.estimated_pick_value
        assert 0.0 < dump.implied_lambda_lower < dump.implied_lambda_upper < 1.0


def test_estimate_revealed_preference_lambda():
    """Verify that model's baseline lambda_3=0.70 is enclosed within empirical bounds."""
    res = estimate_revealed_preference_lambda()

    assert res["is_within_empirical_bounds"] is True
    assert res["implied_lambda_3_lower_bound"] <= 0.70 <= res["implied_lambda_3_upper_bound"]
    assert res["implied_lambda_3_lower_bound"] >= 0.50
    assert res["implied_lambda_3_upper_bound"] <= 0.85
