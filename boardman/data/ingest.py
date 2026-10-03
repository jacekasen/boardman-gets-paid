"""Data ingestion pipeline: Extracts 2025-26 salaries and public metrics from ~/dev/nba and builds master datasets."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from boardman.config import (
    DEFAULT_SEASON,
    FIRST_APRON_2025_26,
    FRICTION_LAMBDA,
    INGESTION_REPORT_JSON,
    LUXURY_TAX_2025_26,
    MASTER_PLAYERS_CSV,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_CSV,
    MASTER_TEAMS_PARQUET,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
    SOURCE_PLAYER_SALARIES,
    SOURCE_PLAYER_SEASONS,
    SOURCE_PLAYER_STATS_RAW,
    SOURCE_TEAM_SALARIES,
    VORP_TO_WAR_MULTIPLIER,
    get_team_bracket,
    normalize_team,
)
from boardman.schema import IngestionReport

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PLAYER_URL_PATTERN = re.compile(r"^https://www\.basketball-reference\.com/players/[a-z]/(?P<id>[a-z0-9]+)\.html$")
NTM_PATTERN = re.compile(r"^\d+TM$")


def extract_player_id(url: Any) -> str | None:
    """Extract player slug (e.g. 'jokicni01') from Basketball-Reference player URL."""
    if pd.isna(url):
        return None
    match = PLAYER_URL_PATTERN.match(str(url).strip())
    return match.group("id") if match else None


def collapse_player_stats(df_stats: pd.DataFrame) -> pd.DataFrame:
    """Collapse raw stats to one record per player_id, preferring aggregate nTM rows for traded players."""
    logger.info("Collapsing multi-team stats rows to one record per player...")
    records: list[pd.Series] = []

    for _, group in df_stats.groupby("player_id"):
        if len(group) == 1:
            records.append(group.iloc[0])
        else:
            ntm_rows = group[group["team_name_abbr"].astype(str).str.match(NTM_PATTERN)]
            if not ntm_rows.empty:
                records.append(ntm_rows.iloc[0])
            else:
                # Fallback to the stint with most minutes played
                records.append(group.sort_values("mp", ascending=False).iloc[0])

    collapsed = pd.DataFrame(records).reset_index(drop=True)
    logger.info("Collapsed %d raw stat rows to %d distinct player stat records.", len(df_stats), len(collapsed))
    return collapsed


def extract_latest_team_map(df_season_stats: pd.DataFrame) -> dict[str, str]:
    """Map each player_id to the franchise abbreviation of their latest regular-season stint.
    Basketball-Reference lists multi-team stints chronologically, with the latest stint last.
    """
    latest_teams: dict[str, str] = {}
    for pid, group in df_season_stats.groupby("player_id"):
        stints = group[~group["team_name_abbr"].astype(str).str.match(NTM_PATTERN)]
        if not stints.empty:
            latest_teams[str(pid)] = normalize_team(stints.iloc[-1]["team_name_abbr"])
        else:
            latest_teams[str(pid)] = normalize_team(group.iloc[0]["team_name_abbr"])
    return latest_teams


def compute_player_experience_map(source_path: Path = SOURCE_PLAYER_STATS_RAW) -> dict[str, int]:
    """Compute number of distinct NBA seasons logged by each player."""
    if not source_path.exists():
        return {}
    try:
        df_stats = pd.read_csv(source_path)
        p_seasons = df_stats.groupby("player_url")["year_id"].nunique().to_dict()
        exp_map: dict[str, int] = {}
        for url, n in p_seasons.items():
            pid = extract_player_id(url)
            if pid:
                exp_map[pid] = int(n)
        return exp_map
    except Exception as e:
        logger.warning("Could not compute experience map: %s", e)
        return {}


def load_raw_stats(source_path: Path, season: str = DEFAULT_SEASON) -> pd.DataFrame:
    """Load raw season stats, record latest stint team, and prepare player_id."""
    if not source_path.exists():
        raise FileNotFoundError(f"Missing raw stats file at {source_path}")

    df = pd.read_csv(source_path)
    season_stats = df[df["year_id"] == season].copy()
    season_stats["player_id"] = season_stats["player_url"].apply(extract_player_id)
    season_stats = season_stats[season_stats["player_id"].notna()].copy()

    latest_teams = extract_latest_team_map(season_stats)
    collapsed = collapse_player_stats(season_stats)
    collapsed["latest_stat_team"] = collapsed["player_id"].map(latest_teams)
    return collapsed


def compute_multiseason_war_prior(
    source_seasons_path: Path = SOURCE_PLAYER_SEASONS,
) -> dict[str, float]:
    """Compute a multi-season blended WAR talent prior from historical player seasons (2023-24, 2024-25).
    Weights recent seasons: 2024-25 (60%) and 2023-24 (40%).
    """
    if not source_seasons_path.exists():
        logger.warning("Historical player seasons file missing at %s; returning empty priors.", source_seasons_path)
        return {}

    try:
        df_hist = pd.read_csv(source_seasons_path)
        recent = df_hist[df_hist["season"].isin(["2023-24", "2024-25"])].copy()
        if recent.empty:
            return {}

        recent["war_vorp"] = recent["vorp"] * VORP_TO_WAR_MULTIPLIER
        w_map = {"2024-25": 0.6, "2023-24": 0.4}
        recent["w"] = recent["season"].map(w_map).fillna(0.5)
        recent["weighted_war"] = recent["war_vorp"] * recent["w"]

        priors: dict[str, float] = {}
        for pid, group in recent.groupby("player_id"):
            w_sum = group["w"].sum()
            if w_sum > 0:
                priors[str(pid)] = float(group["weighted_war"].sum() / w_sum)
        return priors
    except Exception as e:
        logger.warning("Failed computing multiseason WAR prior: %s", e)
        return {}


def build_master_players(
    df_salaries: pd.DataFrame,
    df_stats: pd.DataFrame,
    season: str = DEFAULT_SEASON,
    df_all_salaries: pd.DataFrame | None = None,
    exp_map: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Join salary cap sheets with public box-score impact metrics (VORP, WS, BPM) and multi-season priors."""
    logger.info("Joining %d salary records with %d player stat records...", len(df_salaries), len(df_stats))

    # Keep relevant stat columns
    stat_cols = ["player_id", "team_name_abbr", "games", "mp", "per", "bpm", "vorp", "ws", "ws_per_48"]
    if "latest_stat_team" in df_stats.columns:
        stat_cols.append("latest_stat_team")

    stats_subset = df_stats[stat_cols].rename(columns={"mp": "minutes", "team_name_abbr": "stats_team"})

    # Merge salaries with stats
    merged = pd.merge(df_salaries, stats_subset, on="player_id", how="left")

    # Team code normalization
    merged["team"] = merged["team"].apply(normalize_team)

    def clean_player_name(val: Any) -> str:
        s = str(val).strip()
        try:
            return s.encode("latin1").decode("utf-8")
        except Exception:
            return s

    merged["player_name"] = merged["player_name"].apply(clean_player_name)

    # Impute missing stat metrics for injured / zero-minute players
    merged["is_injured_zero_minutes"] = merged["minutes"].isna() | (merged["minutes"] <= 0)
    merged["games"] = merged["games"].fillna(0).astype(int)
    merged["minutes"] = merged["minutes"].fillna(0.0).astype(float)
    merged["vorp"] = merged["vorp"].fillna(0.0).astype(float)
    merged["ws"] = merged["ws"].fillna(0.0).astype(float)

    # Detect dead money allocations (only for players with multiple salary records where one is stretched/waived)
    multi_salary_pids = set(df_salaries["player_id"].value_counts()[lambda x: x > 1].index)

    # Precompute prior season team mapping for multi-salary players without stats (e.g. Damian Lillard)
    prior_teams_map: dict[str, set[str]] = {}
    if df_all_salaries is not None and not df_all_salaries.empty:
        s_prior = df_all_salaries[df_all_salaries["season"] == "2024-25"]
        if not s_prior.empty:
            for pid, group in s_prior.groupby("player_id"):
                prior_teams_map[str(pid)] = set(group["team"].dropna().apply(normalize_team))
    elif SOURCE_PLAYER_SALARIES.exists():
        try:
            raw_s = pd.read_csv(SOURCE_PLAYER_SALARIES)
            s_prior = raw_s[raw_s["season"] == "2024-25"]
            for pid, group in s_prior.groupby("player_id"):
                prior_teams_map[str(pid)] = set(group["team"].dropna().apply(normalize_team))
        except Exception as e:
            logger.warning("Could not load prior season salaries: %s", e)

    def check_dead_money(row: pd.Series) -> bool:
        pid = str(row["player_id"])
        # If a player has only one salary row, it is their active contracted team, NEVER dead money
        if pid not in multi_salary_pids:
            return False

        t_clean = str(row["team"]).strip()
        latest_team = row.get("latest_stat_team")

        # If player has current season stats, only their latest regular-season stint team is active!
        if pd.notna(latest_team) and str(latest_team).strip() and str(latest_team) != "nan":
            return t_clean != str(latest_team).strip()

        # If no current-season stats available (e.g. injured star like Damian Lillard):
        # The prior-season franchise they actively played for is their active contract;
        # older stretched / waived obligations are DEAD MONEY rows.
        prior_teams = prior_teams_map.get(pid, set())
        if prior_teams:
            return t_clean not in prior_teams

        # Fallback to secondary smaller contract allocation if prior team unknown
        player_rows = df_salaries[df_salaries["player_id"] == pid]
        max_salary = player_rows["salary"].max()
        return bool(row["salary"] < max_salary)

    merged["is_dead_money"] = merged.apply(check_dead_money, axis=1)

    # Invariant enforcement: strictly at most ONE active roster contract per player
    active_mask = ~merged["is_dead_money"]
    duplicate_active_pids = set(merged.loc[active_mask, "player_id"].value_counts()[lambda x: x > 1].index)
    for d_pid in duplicate_active_pids:
        indices = merged[active_mask & (merged["player_id"] == d_pid)].sort_values("salary", ascending=False).index
        merged.loc[indices[1:], "is_dead_money"] = True

    # Compute Wins Above Replacement & Blended WAR
    merged["war_vorp"] = (merged["vorp"] * VORP_TO_WAR_MULTIPLIER).round(2)
    merged["war_blend"] = (0.5 * merged["war_vorp"] + 0.5 * merged["ws"]).round(2)

    # Multi-season blended WAR prior (addresses single-season injury blind spot for Tatum, Haliburton, etc.)
    prior_war_map = compute_multiseason_war_prior()

    def calc_projected_war(row: pd.Series) -> float:
        pid = str(row["player_id"])
        realized = float(row["war_vorp"])
        prior = prior_war_map.get(pid)
        if row["is_injured_zero_minutes"]:
            # If injured with 0 minutes, apply a 25% injury shrinkage discount to their historical talent level
            return round(prior * 0.75, 2) if prior is not None else 0.0
        if prior is not None:
            # Regress current snapshot toward multi-season talent prior (65% realized, 35% prior)
            return round(0.65 * realized + 0.35 * prior, 2)
        return round(realized, 2)

    merged["war_projected"] = merged.apply(calc_projected_war, axis=1)

    # Strict enforcement: all dead money records MUST have 0.0 WAR across all proxies
    merged.loc[merged["is_dead_money"], ["war_vorp", "war_blend", "war_projected"]] = 0.0

    # Explicit handling of known vs missing salaries
    merged["is_salary_known"] = merged["salary"].notna() & (merged["salary"] > 0)
    merged["salary"] = merged["salary"].fillna(0.0).astype(float)
    merged["cap_share"] = merged["cap_share"].fillna(0.0).astype(float)

    # Compute experience and categorize contract tiers
    if exp_map is None:
        exp_map = compute_player_experience_map(SOURCE_PLAYER_STATS_RAW)

    def assign_contract_tier(row: pd.Series) -> str:
        if not row["is_salary_known"]:
            return "Two-Way / Unknown"
        sal = float(row["salary"])
        pid = str(row["player_id"])
        exp = exp_map.get(pid, 5) if exp_map else 5
        if sal >= 35_000_000:
            return "Max / Supermax"
        if exp <= 4 and sal <= 16_000_000:
            return "Rookie Scale"
        if sal >= 8_000_000:
            return "Mid-Level"
        return "Minimum / Rotation"

    merged["contract_tier"] = merged.apply(assign_contract_tier, axis=1)

    # Calculate unconstrained veteran cost per win ($/WAR)
    known_positive = merged[
        (merged["salary"] >= 5_000_000)
        & (merged["war_vorp"] > 0)
        & (~merged["is_dead_money"])
        & (merged["is_salary_known"])
    ]
    if not known_positive.empty and known_positive["war_vorp"].sum() > 0:
        unconstrained_cost_per_win = float(known_positive["salary"].sum() / known_positive["war_vorp"].sum())
    else:
        unconstrained_cost_per_win = 5_193_442.76

    active_players = merged[~merged["is_dead_money"]]
    qa_summary = {
        "season": season,
        "total_salary_records": int(len(df_salaries)),
        "players_with_known_salary": int(merged["is_salary_known"].sum()),
        "players_with_missing_salary": int((~merged["is_salary_known"]).sum()),
        "players_with_stats": int((~merged["is_injured_zero_minutes"]).sum()),
        "players_zero_minutes": int(merged["is_injured_zero_minutes"].sum()),
        "dead_money_allocations": int(merged["is_dead_money"].sum()),
        "duplicate_active_players": int((active_players["player_id"].value_counts() > 1).sum()),
        "unconstrained_cost_per_win": round(unconstrained_cost_per_win, 2),
    }

    final_columns = [
        "player_id",
        "player_name",
        "player_url",
        "season",
        "team",
        "salary",
        "cap_share",
        "is_dead_money",
        "is_salary_known",
        "contract_tier",
        "is_injured_zero_minutes",
        "games",
        "minutes",
        "per",
        "bpm",
        "vorp",
        "ws",
        "ws_per_48",
        "war_vorp",
        "war_blend",
        "war_projected",
    ]

    return merged[final_columns].sort_values("salary", ascending=False).reset_index(drop=True), qa_summary


def build_master_teams(
    df_team_salaries: pd.DataFrame,
    df_players: pd.DataFrame,
    season: str = DEFAULT_SEASON,
) -> pd.DataFrame:
    """Build canonical team payroll and CBA apron bracket status table."""
    logger.info("Computing team payrolls and apron bracket classifications...")

    # Filter to requested season
    teams = df_team_salaries[df_team_salaries["season"] == season].copy()
    teams["team"] = teams["team"].apply(normalize_team)

    records: list[dict[str, Any]] = []
    for _, row in teams.iterrows():
        t = row["team"]
        total_payroll = float(row["team_known_salary_total"])
        bracket, lambda_tax = get_team_bracket(total_payroll)

        # Count active roster players in master table
        roster_count = int((df_players["team"] == t).sum())

        records.append(
            {
                "team": t,
                "season": season,
                "salary_cap": SALARY_CAP_2025_26,
                "luxury_tax": LUXURY_TAX_2025_26,
                "first_apron": FIRST_APRON_2025_26,
                "second_apron": SECOND_APRON_2025_26,
                "total_payroll": total_payroll,
                "total_cap_share": round((total_payroll / SALARY_CAP_2025_26) * 100.0, 2),
                "distance_to_tax": total_payroll - LUXURY_TAX_2025_26,
                "distance_to_first_apron": total_payroll - FIRST_APRON_2025_26,
                "distance_to_second_apron": total_payroll - SECOND_APRON_2025_26,
                "bracket": bracket,
                "lambda_tax": lambda_tax,
                "known_player_count": roster_count,
            }
        )

    df_master_teams = pd.DataFrame(records).sort_values("total_payroll", ascending=False).reset_index(drop=True)
    logger.info("Processed %d team records across all 4 apron brackets.", len(df_master_teams))
    return df_master_teams


def run_ingestion(season: str = DEFAULT_SEASON) -> None:
    """Run full ingestion, merging 2025-26 salaries with stats and saving artifacts."""
    logger.info("Starting Phase 1 data ingestion for season %s...", season)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load player salaries
    if not SOURCE_PLAYER_SALARIES.exists():
        raise FileNotFoundError(f"Missing player salaries at {SOURCE_PLAYER_SALARIES}")
    raw_salaries = pd.read_csv(SOURCE_PLAYER_SALARIES)
    season_salaries = raw_salaries[raw_salaries["season"] == season].copy()
    logger.info("Loaded %d salary records for season %s", len(season_salaries), season)

    # 2. Load player stats
    season_stats = load_raw_stats(SOURCE_PLAYER_STATS_RAW, season=season)

    # 3. Build master players table
    df_players, qa_summary = build_master_players(
        season_salaries,
        season_stats,
        season=season,
        df_all_salaries=raw_salaries,
    )

    # 4. Load team salaries and build master teams table
    if not SOURCE_TEAM_SALARIES.exists():
        raise FileNotFoundError(f"Missing team salaries at {SOURCE_TEAM_SALARIES}")
    raw_team_salaries = pd.read_csv(SOURCE_TEAM_SALARIES)
    df_teams = build_master_teams(raw_team_salaries, df_players, season=season)

    # 5. Add team bracket distribution to QA summary
    bracket_counts = df_teams["bracket"].value_counts().to_dict()
    qa_summary.update(
        {
            "total_teams": len(df_teams),
            "teams_bracket_0_sub_tax": int(bracket_counts.get(0, 0)),
            "teams_bracket_1_tax": int(bracket_counts.get(1, 0)),
            "teams_bracket_2_first_apron": int(bracket_counts.get(2, 0)),
            "teams_bracket_3_second_apron": int(bracket_counts.get(3, 0)),
        }
    )

    # Validate with Pydantic
    report = IngestionReport(**qa_summary)

    # 6. Save Parquet and CSV artifacts
    df_players.to_parquet(MASTER_PLAYERS_PARQUET, index=False)
    df_players.to_csv(MASTER_PLAYERS_CSV, index=False)
    logger.info("Saved master players table to %s (%d rows)", MASTER_PLAYERS_PARQUET, len(df_players))

    df_teams.to_parquet(MASTER_TEAMS_PARQUET, index=False)
    df_teams.to_csv(MASTER_TEAMS_CSV, index=False)
    logger.info("Saved master teams table to %s (%d rows)", MASTER_TEAMS_PARQUET, len(df_teams))

    INGESTION_REPORT_JSON.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    logger.info("Saved QA ingestion report to %s", INGESTION_REPORT_JSON)

    # Print summary
    print("\n" + "=" * 60)
    print("BOARD MAN GETS PAID - DATA INGESTION SUMMARY (2025-26)")
    print("=" * 60)
    print(f"Total Salary Records:       {report.total_salary_records:,}")
    print(f"Players with Known Salary:  {report.players_with_known_salary:,}")
    print(f"Players with Active Stats:  {report.players_with_stats:,}")
    print(f"Players Zero Minutes:       {report.players_zero_minutes:,}")
    print(f"Total Franchises:           {report.total_teams}")
    print(f" - Bracket 0 (< Tax):       {report.teams_bracket_0_sub_tax} teams")
    print(f" - Bracket 1 (Tax to 1st):  {report.teams_bracket_1_tax} teams")
    print(f" - Bracket 2 (1st to 2nd):  {report.teams_bracket_2_first_apron} teams")
    print(f" - Bracket 3 (> 2nd Apron): {report.teams_bracket_3_second_apron} teams")
    print(f"Unconstrained $/WAR:        ${report.unconstrained_cost_per_win:,.2f}")
    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=DEFAULT_SEASON, help="Season to ingest (default: 2025-26)")
    args = parser.parse_args()
    run_ingestion(season=args.season)


if __name__ == "__main__":
    main()
