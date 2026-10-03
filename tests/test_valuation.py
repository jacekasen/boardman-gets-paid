"""Unit tests for valuation engine: Fair Value, Net Surplus, and Efficiency."""

import json

import pandas as pd
import pytest

from boardman.config import (
    INGESTION_REPORT_JSON,
    MASTER_PLAYERS_PARQUET,
    MINIMUM_SALARY_2025_26,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
)
from boardman.valuation import (
    DEFAULT_COST_PER_WIN,
    REPLACEMENT_SALARY,
    VETERAN_CALIBRATION_FLOOR,
    build_league_surplus_board,
    calculate_player_valuation,
    calibrate_cost_per_win,
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
    assert val.fair_value == pytest.approx(REPLACEMENT_SALARY + 5.0 * DEFAULT_COST_PER_WIN, rel=1e-3)
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
    expected_roi = round((REPLACEMENT_SALARY + 4.0 * DEFAULT_COST_PER_WIN) / 10_000_000.0, 2)
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
    assert val_unknown.surplus_efficiency is None
    assert val_unknown.gross_surplus is None
    assert val_unknown.net_surplus is None


def test_replacement_level_player_on_minimum_breaks_even():
    """A 0-WAR player on the league minimum is exactly replacement level: zero surplus."""
    player = {
        "player_id": "repl01",
        "player_name": "Replacement Player",
        "team": "SAS",
        "salary": float(MINIMUM_SALARY_2025_26),
        "war_projected": 0.0,
    }
    val = calculate_player_valuation(player, team_payroll=150_000_000.0)
    assert val.gross_surplus == pytest.approx(0.0, abs=0.01)
    assert val.roi_multiple == 1.0


def test_cost_per_win_single_source_of_truth():
    """The default constant, the ingestion report, and a fresh calibration must agree."""
    report = json.loads(INGESTION_REPORT_JSON.read_text(encoding="utf-8"))
    calibrated = calibrate_cost_per_win(pd.read_parquet(MASTER_PLAYERS_PARQUET))
    assert calibrated == pytest.approx(report["unconstrained_cost_per_win"], abs=0.01)
    assert DEFAULT_COST_PER_WIN == pytest.approx(calibrated, abs=0.01)


def test_veteran_pool_prices_at_zero_aggregate_surplus():
    """C_w is the market price of a win, so the calibration pool nets to zero gross surplus."""
    df_board = build_league_surplus_board()
    pool = df_board[
        (df_board["salary"] >= VETERAN_CALIBRATION_FLOOR)
        & ~df_board["is_dead_money"]
        & df_board["is_salary_known"]
    ]
    assert pool["gross_surplus"].sum() == pytest.approx(0.0, abs=1_000.0)


def test_unverified_salaries_never_rank_as_surplus():
    """Unverified salaries carry no surplus and sort below every verified contract."""
    df_board = build_league_surplus_board()
    unknown = df_board[~df_board["is_salary_known"] & ~df_board["is_dead_money"]]
    assert len(unknown) > 0
    assert unknown["net_surplus"].isna().all()
    first_unknown = df_board["net_surplus"].isna().idxmax()
    assert df_board.loc[first_unknown:, "net_surplus"].isna().all()

