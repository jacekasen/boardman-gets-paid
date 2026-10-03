"""Unit tests for valuation engine: Fair Value, GSV, Apron Friction, and Roster Delta."""

import pandas as pd
import pytest

from boardman.config import (
    FIRST_APRON_2025_26,
    FRICTION_LAMBDA,
    LUXURY_TAX_2025_26,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
)
from boardman.valuation import (
    DEFAULT_COST_PER_WIN,
    build_league_surplus_board,
    calculate_player_valuation,
    calculate_roster_delta,
    calculate_roster_valuation,
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

    # 1. Contract of $20M
    sal1 = 20_000_000.0
    _, _, f1 = compute_apron_friction(sal1, team_payroll)
    expected_f1 = 0.70 * sal1 * (sal1 / SALARY_CAP_2025_26)
    assert f1 == pytest.approx(expected_f1, rel=1e-3)

    # 2. Contract of $40M (doubled)
    sal2 = 40_000_000.0
    _, _, f2 = compute_apron_friction(sal2, team_payroll)
    expected_f2 = 0.70 * sal2 * (sal2 / SALARY_CAP_2025_26)
    assert f2 == pytest.approx(expected_f2, rel=1e-3)

    # Quadratic property: Doubling the salary quadruples the friction tax
    assert f2 / f1 == pytest.approx(4.0, rel=1e-3)


def test_uncle_dennis_circumvention_modifier():
    """Test off-the-cap cash additions (e.g. Kawhi Aspiration deals) reduce net surplus."""
    player = {
        "player_id": "leonaka01",
        "player_name": "Kawhi Leonard",
        "team": "LAC",
        "salary": 50_000_000.0,
        "war_vorp": 10.0,
    }
    payroll = 185_000_000.0

    # Clean valuation
    val_clean = calculate_player_valuation(player, team_payroll=payroll, uncle_dennis_cash=0.0)

    # Circumvention deal: $7,000,000 annual off-the-cap endorsement
    val_off_cap = calculate_player_valuation(player, team_payroll=payroll, uncle_dennis_cash=7_000_000.0)

    assert val_off_cap.uncle_dennis_cash == 7_000_000.0
    assert val_off_cap.gross_surplus == pytest.approx(val_clean.gross_surplus - 7_000_000.0)
    assert val_off_cap.net_surplus == pytest.approx(val_clean.net_surplus - 7_000_000.0)


def test_roster_delta_bracket_transition_relief():
    """Verify that shedding salary and dropping from 2nd Apron (Bracket 3) to Tax (Bracket 1) creates massive roster-wide friction relief."""
    pre_roster = [
        {"player_id": "star1", "player_name": "Star 1", "salary": 50_000_000.0, "war_vorp": 8.0},
        {"player_id": "star2", "player_name": "Star 2", "salary": 45_000_000.0, "war_vorp": 7.0},
        {"player_id": "vet1", "player_name": "Vet 1", "salary": 30_000_000.0, "war_vorp": 2.0},  # Traded away
        {"player_id": "role1", "player_name": "Role 1", "salary": 20_000_000.0, "war_vorp": 3.0},
        {"player_id": "role2", "player_name": "Role 2", "salary": 15_000_000.0, "war_vorp": 2.5},
        {"player_id": "bench1", "player_name": "Bench 1", "salary": 10_000_000.0, "war_vorp": 1.5},
        {"player_id": "bench2", "player_name": "Bench 2", "salary": 10_000_000.0, "war_vorp": 1.0},
        {"player_id": "bench3", "player_name": "Bench 3", "salary": 30_000_000.0, "war_vorp": 1.0},
    ]
    pre_payroll = 210_000_000.0  # Above Second Apron ($207.8M) -> Bracket 3 (lambda = 0.70)

    # Trade: Vet 1 ($30M, 2.0 WAR) is traded for Young Player ($10M, 2.0 WAR), shedding $20M
    post_roster = [
        {"player_id": "star1", "player_name": "Star 1", "salary": 50_000_000.0, "war_vorp": 8.0},
        {"player_id": "star2", "player_name": "Star 2", "salary": 45_000_000.0, "war_vorp": 7.0},
        {"player_id": "young1", "player_name": "Young 1", "salary": 10_000_000.0, "war_vorp": 2.0},
        {"player_id": "role1", "player_name": "Role 1", "salary": 20_000_000.0, "war_vorp": 3.0},
        {"player_id": "role2", "player_name": "Role 2", "salary": 15_000_000.0, "war_vorp": 2.5},
        {"player_id": "bench1", "player_name": "Bench 1", "salary": 10_000_000.0, "war_vorp": 1.5},
        {"player_id": "bench2", "player_name": "Bench 2", "salary": 10_000_000.0, "war_vorp": 1.0},
        {"player_id": "bench3", "player_name": "Bench 3", "salary": 30_000_000.0, "war_vorp": 1.0},
    ]
    post_payroll = 190_000_000.0  # Between Tax ($187.9M) and First Apron ($195.9M) -> Bracket 1 (lambda = 0.15)

    delta = calculate_roster_delta(
        team_code="TEST",
        pre_roster=pre_roster,
        post_roster=post_roster,
        pre_payroll=pre_payroll,
        post_payroll=post_payroll,
    )

    assert delta.pre_bracket == 3
    assert delta.post_bracket == 1
    assert "BRACKET SHIFT" in delta.bracket_transition
    assert delta.friction_relief > 10_000_000.0, "Dropping from Bracket 3 to 1 must produce massive friction relief"
    assert delta.delta_nsv > 0, "Net surplus must rise significantly due to freed roster mobility"


def test_league_surplus_board():
    """Verify building the full league surplus leaderboard."""
    df_board = build_league_surplus_board()
    assert len(df_board) > 500
    assert "net_surplus" in df_board.columns
    assert "gross_surplus" in df_board.columns
    assert "friction_tax" in df_board.columns
    assert "surplus_efficiency" in df_board.columns

    # Leaderboard should be ordered by net_surplus descending
    assert df_board.iloc[0]["net_surplus"] >= df_board.iloc[1]["net_surplus"]

    # Top players should have substantial positive surplus
    top_player = df_board.iloc[0]
    assert top_player["net_surplus"] > 50_000_000.0
