"""JSON bridge for the Next.js frontend; calculations stay in the Python engine."""

from __future__ import annotations

import json
import sys

import pandas as pd

from boardman.config import (
    CANONICAL_TEAM_NAMES, MASTER_PLAYERS_PARQUET, MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26, LUXURY_TAX_2025_26, FIRST_APRON_2025_26,
    SECOND_APRON_2025_26,
)
from boardman.trade_engine import evaluate_trade
from boardman.valuation import build_league_surplus_board, DEFAULT_COST_PER_WIN


def snapshot() -> dict:
    players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    teams = pd.read_parquet(MASTER_TEAMS_PARQUET)
    board = build_league_surplus_board(df_players=players, df_teams=teams)
    dead_ids = set(players.loc[players["is_dead_money"], "player_id"])
    records = board.to_dict(orient="records")
    for player in records:
        player["is_dead_money"] = player["player_id"] in dead_ids
    return {
        "season": "2025–26", "metric": "Multi-season WAR", "costPerWin": DEFAULT_COST_PER_WIN,
        "thresholds": {"cap": SALARY_CAP_2025_26, "tax": LUXURY_TAX_2025_26,
                       "first": FIRST_APRON_2025_26, "second": SECOND_APRON_2025_26},
        "players": records,
        "teams": [{**t, "name": CANONICAL_TEAM_NAMES[t["team"]]} for t in teams.to_dict(orient="records")],
    }


def trade(payload: dict) -> dict:
    for key in ("team_a", "team_b"):
        if payload.get(key) not in CANONICAL_TEAM_NAMES:
            raise ValueError("Select a valid team on each side.")
    for key in ("send_a", "send_b"):
        ids = payload.get(key)
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            raise ValueError("Player selections must be lists of identifiers.")
        if len(ids) > 15 or len(ids) != len(set(ids)):
            raise ValueError("Select each player only once, up to 15 players per team.")
    if not payload["send_a"] and not payload["send_b"]:
        raise ValueError("Select at least one player to evaluate a trade.")
    return evaluate_trade(team_a=payload["team_a"], team_b=payload["team_b"],
                          send_a=payload["send_a"], send_b=payload["send_b"]).model_dump()


if __name__ == "__main__":
    try:
        result = snapshot() if sys.argv[1:] == ["snapshot"] else trade(json.load(sys.stdin))
        print(json.dumps(result, allow_nan=False))
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(2)
