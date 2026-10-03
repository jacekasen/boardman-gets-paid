"""Configuration, directory paths, team aliases, and 2025-26 statutory CBA financial thresholds."""

from pathlib import Path

# Repository root and local data paths
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Source data paths in local nba monorepo
NBA_SOURCE_DIR = Path.home() / "dev" / "nba" / "data"
SOURCE_PLAYER_SALARIES = NBA_SOURCE_DIR / "modeling" / "player_salaries.csv"
SOURCE_TEAM_SALARIES = NBA_SOURCE_DIR / "modeling" / "team_season_salaries.csv"
SOURCE_PLAYER_SEASONS = NBA_SOURCE_DIR / "modeling" / "player_seasons.csv"
SOURCE_PLAYER_STATS_RAW = NBA_SOURCE_DIR / "nba_player_stats.csv"

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

# Apron Friction Multipliers lambda(T)
# Hypothesized opportunity-cost breakdown based on statutory 2023 CBA penalties:
# - Bracket 1 (Tax, lambda=0.15): Marginal cash tax drag ($1.50-$2.50/dollar) without operational bans.
# - Bracket 2 (1st Apron, lambda=0.35): Hard 100% salary matching + forfeiture of Bi-Annual Exception (~$4.7M asset).
# - Bracket 3 (2nd Apron, lambda=0.70): Estimated from an assumed statutory cost breakdown:
#     1. Frozen 1st-round draft pick 7 years out & demoted to pick 30: ~$7.3M estimated rookie surplus loss.
#     2. Forfeiture of Taxpayer Mid-Level Exception: ~$5.4M estimated replacement cost.
#     3. Zero salary aggregation liquidity haircut: 10%-15% illiquidity discount (~$7M-$10M).
#     4. Repeater luxury tax surcharges ($3.75-$4.75+/dollar).
#     Total annualized drag on a 2nd Apron contender is ~$25M-$32M, which lambda=0.70 approximates on CLE ($31.1M).
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
