"""Tests for data ingestion, master table construction, and schema validation."""

import json
import pandas as pd
import pytest

from boardman.config import (
    FIRST_APRON_2025_26,
    FRICTION_LAMBDA,
    INGESTION_REPORT_JSON,
    LUXURY_TAX_2025_26,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
    get_team_bracket,
    normalize_team,
)
from boardman.schema import IngestionReport, PlayerRecord, TeamRecord


def test_team_normalization():
    """Verify team code normalization handles aliases and canonical codes."""
    assert normalize_team("BKN") == "BRK"
    assert normalize_team("PHX") == "PHO"
    assert normalize_team("CHA") == "CHO"
    assert normalize_team("bos") == "BOS"
    assert normalize_team("DEN") == "DEN"


def test_get_team_bracket_thresholds():
    """Verify team bracket and friction lambda mapping across thresholds."""
    # Sub-tax bracket 0
    b0, l0 = get_team_bracket(150_000_000)
    assert b0 == 0
    assert l0 == FRICTION_LAMBDA[0] == 0.00

    # Tax to First Apron bracket 1
    b1, l1 = get_team_bracket(LUXURY_TAX_2025_26 + 100_000)
    assert b1 == 1
    assert l1 == FRICTION_LAMBDA[1] == 0.15

    # First to Second Apron bracket 2
    b2, l2 = get_team_bracket(FIRST_APRON_2025_26 + 500_000)
    assert b2 == 2
    assert l2 == FRICTION_LAMBDA[2] == 0.35

    # Above Second Apron bracket 3
    b3, l3 = get_team_bracket(SECOND_APRON_2025_26 + 1_000_000)
    assert b3 == 3
    assert l3 == FRICTION_LAMBDA[3] == 0.70


def test_master_teams_integrity():
    """Verify master teams parquet exists, has 30 teams, and clean payroll metrics."""
    assert MASTER_TEAMS_PARQUET.exists(), "Master teams parquet file missing"
    df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    assert len(df_teams) == 30, "NBA must have exactly 30 franchises"
    assert df_teams["team"].nunique() == 30, "Team abbreviations must be distinct"

    for _, row in df_teams.iterrows():
        # Validate through Pydantic
        record = TeamRecord(**row.to_dict())
        assert record.total_payroll > 0
        assert record.bracket in (0, 1, 2, 3)
        assert record.lambda_tax in (0.00, 0.15, 0.35, 0.70)
        assert record.salary_cap == SALARY_CAP_2025_26


def test_master_players_integrity():
    """Verify master players parquet exists and critical columns have no NaNs."""
    assert MASTER_PLAYERS_PARQUET.exists(), "Master players parquet file missing"
    df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)

    assert len(df_players) >= 500, "Expected at least 500 player contracts"
    assert df_players["salary"].isna().sum() == 0, "Salaries must not be NaN"
    assert df_players["vorp"].isna().sum() == 0, "VORP must not be NaN"
    assert df_players["ws"].isna().sum() == 0, "WS must not be NaN"
    assert df_players["war_vorp"].isna().sum() == 0, "WAR (VORP) must not be NaN"

    # Verify superstar presence and metrics
    jokic = df_players[df_players["player_id"] == "jokicni01"]
    assert not jokic.empty, "Nikola Jokic must be in master players"
    assert jokic.iloc[0]["salary"] > 50_000_000
    assert jokic.iloc[0]["war_vorp"] > 20.0

    kawhi = df_players[df_players["player_id"] == "leonaka01"]
    assert not kawhi.empty, "Kawhi Leonard must be in master players"
    assert kawhi.iloc[0]["salary"] == 50_000_000.0
    assert kawhi.iloc[0]["war_vorp"] > 10.0


def test_ingestion_report_validity():
    """Verify ingestion_report.json conforms to IngestionReport schema."""
    assert INGESTION_REPORT_JSON.exists(), "Ingestion report JSON missing"
    raw_data = json.loads(INGESTION_REPORT_JSON.read_text(encoding="utf-8"))
    report = IngestionReport(**raw_data)

    assert report.total_teams == 30
    assert report.total_salary_records >= 600
    assert report.unconstrained_cost_per_win > 3_000_000
