"""Configuration, directory paths, and 2025-26 statutory CBA financial thresholds."""

from pathlib import Path

# Repository root and local data paths
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Source data path in local nba monorepo
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

# Public Metric Calibration Constants
VORP_TO_WAR_MULTIPLIER = 2.70
REPLACEMENT_LEVEL_BPM = -2.0

# Apron Friction Multipliers lambda(T)
# Quantifies the roster immobility and transactional penalty drag
FRICTION_LAMBDA = {
    0: 0.00,  # Below Luxury Tax: Full flexibility, no tax penalty
    1: 0.15,  # Tax to First Apron: Cash tax penalties, Bi-annual exception preserved
    2: 0.35,  # First to Second Apron: Hard salary matching, loss of bi-annual exception
    3: 0.70,  # Above Second Apron: Frozen draft picks, no salary aggregation, no cash
}
