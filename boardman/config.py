"""Configuration, directory paths, team aliases, and 2025-26 statutory CBA financial thresholds."""

from pathlib import Path
from typing import Any


# Repository root and local data paths
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Source data paths: prefer in-repo data/raw directory, fallback to local ~/dev/nba if needed
NBA_SOURCE_DIR = Path.home() / "dev" / "nba" / "data"


def _resolve_source_path(rel_path: str) -> Path:
    local_path = RAW_DATA_DIR / rel_path
    if local_path.exists():
        return local_path
    external_path = NBA_SOURCE_DIR / rel_path
    if external_path.exists():
        return external_path
    return local_path


SOURCE_PLAYER_SALARIES = _resolve_source_path("modeling/player_salaries.csv")
SOURCE_TEAM_SALARIES = _resolve_source_path("modeling/team_season_salaries.csv")
SOURCE_PLAYER_SEASONS = _resolve_source_path("modeling/player_seasons.csv")
SOURCE_PLAYER_STATS_RAW = _resolve_source_path("nba_player_stats.csv")

# Target processed data outputs
MASTER_PLAYERS_PARQUET = PROCESSED_DATA_DIR / "master_players_2025_26.parquet"
MASTER_PLAYERS_CSV = PROCESSED_DATA_DIR / "master_players_2025_26.csv"
MASTER_TEAMS_PARQUET = PROCESSED_DATA_DIR / "master_teams_2025_26.parquet"
MASTER_TEAMS_CSV = PROCESSED_DATA_DIR / "master_teams_2025_26.csv"
INGESTION_REPORT_JSON = PROCESSED_DATA_DIR / "ingestion_report.json"

# 2025-26 Official League Financial Thresholds (in USD)
DEFAULT_SEASON = "2025-26"
SALARY_CAP_2025_26 = 154_647_000
LUXURY_TAX_2025_26 = 187_895_000
FIRST_APRON_2025_26 = 195_945_000
SECOND_APRON_2025_26 = 207_824_000
MINIMUM_SALARY_2025_26 = 2_100_000

# 2023 CBA Article VII, Section 6(j) Trade Band Escalation:
# The statutory trade bands are indexed to Salary Cap growth since 2023-24 ($136,021,000).
SALARY_CAP_2023_24_BASE = 136_021_000
CBA_CAP_INFLATION_2025_26 = SALARY_CAP_2025_26 / SALARY_CAP_2023_24_BASE  # ~1.136934

# 2025-26 Escalated Matching Thresholds (Article VII, Section 6(j)(1)-(3))
BAND_1_THRESHOLD_2025_26 = round(7_500_000 * CBA_CAP_INFLATION_2025_26)      # $8,527,011
BAND_2_THRESHOLD_2025_26 = round(29_000_000 * CBA_CAP_INFLATION_2025_26)     # $32,971,107
TRADE_BUFFER_ALLOWANCE_2025_26 = round(250_000 * CBA_CAP_INFLATION_2025_26) # $284,234

# Public Metric Calibration Constants
VORP_TO_WAR_MULTIPLIER = 2.70
REPLACEMENT_LEVEL_BPM = -2.0
DEFAULT_METRIC = "war_projected"

# Sourced 2023 CBA Second Apron Cost Components (Annualized Economic Drag)
# Used to ground lambda_3 in statutory rules and empirical sports economics literature
SECOND_APRON_COST_COMPONENTS: list[dict[str, Any]] = [
    {
        "component_id": "frozen_draft_pick",
        "name": "Frozen 1st-Round Draft Pick & Demotion to Pick 30",
        "statutory_basis": "2023 CBA Article VII, Section 7(g)",
        "citation": "FiveThirtyEight / Kevin Pelton (ESPN) / Cranston draft surplus curves (middle-first #15-#20: $10.5M 4-yr rookie surplus vs pick #30: $3.2M)",
        "description": "7-year-out first-round pick frozen from trade; demoted to pick 30 if team remains in Second Apron 2 of 4 years.",
        "low_usd": 6_000_000.0,
        "high_usd": 8_500_000.0,
        "midpoint_usd": 7_300_000.0,
    },
    {
        "component_id": "lost_tp_mle",
        "name": "Forfeiture of Taxpayer Mid-Level Exception (TP-MLE)",
        "statutory_basis": "2023 CBA Article VII, Section 6(b)(iii)",
        "citation": "Spotrac / HoopsHype contract market value for rotation-level taxpayer MLE signings ($5.18M-$5.70M AAV in 2024-2026)",
        "description": "Second Apron teams are statutorily barred from using the Taxpayer Mid-Level Exception to sign veteran rotation contributors.",
        "low_usd": 4_800_000.0,
        "high_usd": 6_200_000.0,
        "midpoint_usd": 5_400_000.0,
    },
    {
        "component_id": "aggregation_illiquidity",
        "name": "Trade Aggregation & Cash Ban Illiquidity Haircut",
        "statutory_basis": "2023 CBA Article VII, Section 8(e)",
        "citation": "Asset transfer illiquidity discount literature (Amihud & Mendelson 1986; Silber 1991: 10%-15% discount on movable salary base)",
        "description": "Prohibition on aggregating salaries, taking back more salary than sent, or sending cash in trades.",
        "low_usd": 6_500_000.0,
        "high_usd": 10_500_000.0,
        "midpoint_usd": 8_000_000.0,
    },
    {
        "component_id": "repeater_and_buyout",
        "name": "Repeater Tax Surcharge Drag & Buyout Market Ban",
        "statutory_basis": "2023 CBA Article VII, Section 8(c) & Section 12",
        "citation": "Larry Coon CBA FAQ and historical repeater tax acceleration schedules on contending rosters ($3.75-$4.75+/dollar)",
        "description": "Escalating multi-tier luxury tax rates plus prohibition on signing buyout-market free agents making above MLE.",
        "low_usd": 6_000_000.0,
        "high_usd": 11_000_000.0,
        "midpoint_usd": 8_500_000.0,
    },
]

# Total annualized drag across the 4 components: $23.3M - $36.2M (midpoint ~$29.2M)
# Across Cleveland's roster quadratic base ($44.39M), this implies lambda_3 in [0.525, 0.816] (midpoint ~0.66)

# Apron Friction Multipliers lambda(T)
# - Bracket 1 (Tax, lambda=0.15): Marginal cash tax drag ($1.50-$2.50/dollar) without operational bans.
# - Bracket 2 (1st Apron, lambda=0.35): Hard 100% salary matching + forfeiture of Bi-Annual Exception (~$4.7M asset).
# - Bracket 3 (2nd Apron, lambda=0.70): Baseline operational drag calibrated from the 4 statutory cost components (~$29M-$31M).
FRICTION_LAMBDA = {
    0: 0.00,  # Below Luxury Tax: Full flexibility, no tax penalty
    1: 0.15,  # Tax to First Apron: Cash tax penalties, Bi-annual exception preserved
    2: 0.35,  # First to Second Apron: Hard salary matching, loss of bi-annual exception
    3: 0.70,  # Above Second Apron: Frozen draft picks, no salary aggregation, no cash
}


# Team code normalization (Basketball-Reference codes <-> Standard NBA codes)
TEAM_ALIASES = {
    "BKN": "BRK",
    "CHA": "CHO",
    "PHX": "PHO",
}

CANONICAL_TEAM_NAMES = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BRK": "Brooklyn Nets",
    "CHO": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "LA Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHO": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards",
}


def normalize_team(team: str) -> str:
    """Normalize input team string to internal 3-letter abbreviation."""
    cleaned = str(team).strip().upper()
    return TEAM_ALIASES.get(cleaned, cleaned)


def get_team_bracket(
    total_payroll: float,
    friction_lambda: dict[int, float] | None = None,
) -> tuple[int, float]:
    """Return the apron bracket (0, 1, 2, 3) and friction lambda for a given payroll."""
    lam_map = friction_lambda if friction_lambda is not None else FRICTION_LAMBDA
    if total_payroll >= SECOND_APRON_2025_26:
        return 3, lam_map.get(3, 0.0)
    if total_payroll >= FIRST_APRON_2025_26:
        return 2, lam_map.get(2, 0.0)
    if total_payroll >= LUXURY_TAX_2025_26:
        return 1, lam_map.get(1, 0.0)
    return 0, lam_map.get(0, 0.0)
