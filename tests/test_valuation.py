"""Unit tests for valuation engine: Fair Value, Net Surplus, and Efficiency."""

import pytest

from boardman.config import (
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
)
from boardman.valuation import (
    DEFAULT_COST_PER_WIN,
    build_league_surplus_board,
    calculate_player_valuation,
    compute_apron_friction,
)


def test_sub_tax_zero_friction():
    """Players on sub-tax teams (Bracket 0) experience zero apron friction."""
    player = {
        "player_id": "test01",
        "player_name": "Test Player",
        "team": "SAS",
        "salary": 20_000_000.0,
        "war_vorp": 5.0,
    }
    sub_tax_payroll = 140_000_000.0
    val = calculate_player_valuation(player, team_payroll=sub_tax_payroll)

    assert val.bracket == 0
    assert val.lambda_tax == 0.00
    assert val.friction_tax == 0.00
    assert val.fair_value == pytest.approx(5.0 * DEFAULT_COST_PER_WIN, rel=1e-3)
    assert val.gross_surplus == val.net_surplus


def test_apron_friction_quadratic_scaling():
    """Verify quadratic scaling of the apron friction tax under Bracket 3 (Second Apron)."""
    team_payroll = SECOND_APRON_2025_26 + 5_000_000.0  # Bracket 3, lambda = 0.70

    sal1 = 20_000_000.0
    _, _, f1 = compute_apron_friction(sal1, team_payroll)
    expected_f1 = 0.70 * sal1 * (sal1 / SALARY_CAP_2025_26)
    assert f1 == pytest.approx(expected_f1, rel=1e-3)

    sal2 = 40_000_000.0
    _, _, f2 = compute_apron_friction(sal2, team_payroll)
    expected_f2 = 0.70 * sal2 * (sal2 / SALARY_CAP_2025_26)
    assert f2 == pytest.approx(expected_f2, rel=1e-3)

    assert f2 / f1 == pytest.approx(4.0, rel=1e-3)


def test_league_surplus_board():
    """Verify building the full league surplus leaderboard."""
    df_board = build_league_surplus_board()
    assert len(df_board) > 500
    assert "net_surplus" in df_board.columns
    assert "gross_surplus" in df_board.columns
    assert "surplus_efficiency" in df_board.columns

    # Leaderboard should be ordered by net_surplus descending
    assert df_board.iloc[0]["net_surplus"] >= df_board.iloc[1]["net_surplus"]
    top_player = df_board.iloc[0]
    assert top_player["net_surplus"] > 50_000_000.0
    assert "roi_multiple" in df_board.columns
    assert "contract_tier" in df_board.columns


def test_dead_money_valuation_properties():
    """Flagged dead money contracts must have zero WAR, zero fair value, and negative gross surplus."""
    dead_player = {
        "player_id": "waived01",
        "player_name": "Waived Player",
        "team": "MEM",
        "salary": 9_000_000.0,
        "war_vorp": 2.5,
        "is_dead_money": True,
    }
    val = calculate_player_valuation(dead_player, team_payroll=150_000_000.0)
    assert val.is_dead_money is True
    assert val.war == 0.0
    assert val.fair_value == 0.0
    assert val.gross_surplus == -9_000_000.0
    assert val.net_surplus == -9_000_000.0
    assert val.friction_tax == 0.0
    assert val.roi_multiple == 0.0


def test_roi_multiple_and_unknown_salary():
    """Verify ROI multiple is calculated for known salaries and None for missing salaries."""
    known = {
        "player_id": "star01",
        "player_name": "Star Player",
        "team": "OKC",
        "salary": 10_000_000.0,
        "war_projected": 4.0,
        "is_salary_known": True,
    }
    val_known = calculate_player_valuation(known, team_payroll=150_000_000.0)
    expected_roi = round((4.0 * DEFAULT_COST_PER_WIN) / 10_000_000.0, 2)
    assert val_known.roi_multiple == expected_roi

    unknown = {
        "player_id": "twoway01",
        "player_name": "Two Way Player",
        "team": "MIA",
        "salary": 0.0,
        "war_projected": 1.0,
        "is_salary_known": False,
    }
    val_unknown = calculate_player_valuation(unknown, team_payroll=150_000_000.0)
    assert val_unknown.roi_multiple is None
    assert val_unknown.surplus_efficiency == 0.0

