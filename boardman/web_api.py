"""JSON bridge for the Next.js frontend; contract surplus valuations and team efficiency."""

from __future__ import annotations

import json
import math
import sys

import pandas as pd

from boardman.config import (
    CANONICAL_TEAM_NAMES,
    DEFAULT_SEASON,
    FIRST_APRON_2025_26,
    LUXURY_TAX_2025_26,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
)
from boardman.valuation import REPLACEMENT_SALARY, build_league_surplus_board, calibrate_cost_per_win


def snapshot() -> dict:
    players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    teams = pd.read_parquet(MASTER_TEAMS_PARQUET)
    cost_per_win = calibrate_cost_per_win(players)
    board = build_league_surplus_board(df_players=players, df_teams=teams, cost_per_win=cost_per_win)
    raw_records = board.to_dict(orient="records")
    records = [
        {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v) for k, v in r.items()}
        for r in raw_records
    ]
    return {
        "season": DEFAULT_SEASON,
        "metric": "Multi-season WAR",
        "costPerWin": round(cost_per_win, 2),
        "replacementSalary": REPLACEMENT_SALARY,
        "thresholds": {
            "cap": SALARY_CAP_2025_26,
            "tax": LUXURY_TAX_2025_26,
            "first": FIRST_APRON_2025_26,
            "second": SECOND_APRON_2025_26,
        },
        "players": records,
        "teams": [{**t, "name": CANONICAL_TEAM_NAMES[t["team"]]} for t in teams.to_dict(orient="records")],
    }


if __name__ == "__main__":
    try:
        result = snapshot()
        print(json.dumps(result, allow_nan=False))
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(2)
