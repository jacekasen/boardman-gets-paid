"""Trade simulator engine: Evaluates CBA legality, salary matching, apron bans, and Net Surplus swings (Delta NSV)."""

from __future__ import annotations

import unicodedata
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from boardman.cba_rules import TradeComplianceCheck, check_trade_compliance
from boardman.config import (
    DEFAULT_SEASON,
    MASTER_PLAYERS_PARQUET,
    MASTER_TEAMS_PARQUET,
    SALARY_CAP_2025_26,
    normalize_team,
)
from boardman.schema import PlayerRecord
from boardman.valuation import (
    DEFAULT_COST_PER_WIN,
    RosterDelta,
    calculate_roster_delta,
)


def _clean_mojibake(text: str) -> str:
    """Attempt to repair common latin1/utf-8 double-encoding artifacts."""
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


def _normalize_name_lookup(name: str) -> str:
    """Normalize names for case-insensitive, accent-insensitive, and mojibake-safe lookup."""
    cleaned = _clean_mojibake(name)
    nfkd = unicodedata.normalize("NFKD", cleaned)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    return "".join(c for c in ascii_text.lower() if c.isalnum())


class TradeEvaluation(BaseModel):
    """Complete analytical and legal evaluation of a proposed trade between two franchises."""

    is_legal: bool
    season: str = DEFAULT_SEASON
    team_a: str
    team_b: str
    send_a: list[str]
    send_b: list[str]
    salary_out_a: float
    salary_in_a: float
    salary_out_b: float
    salary_in_b: float
    cash_a_to_b: float = 0.0
    compliance_a: TradeComplianceCheck
    compliance_b: TradeComplianceCheck
    delta_a: RosterDelta
    delta_b: RosterDelta
    violations: list[str] = Field(default_factory=list)

    def summary(self) -> str:
        """Render a clean, human-readable summary of the trade result."""
        status = "[LEGAL CBA TRANSACTION]" if self.is_legal else "[ILLEGAL CBA TRANSACTION]"
        lines = [
            "=" * 64,
            f"BOARD MAN TRADE EVALUATION: {self.team_a} <-> {self.team_b}",
            f"STATUS: {status}",
            "=" * 64,
            "",
            f"--- {self.team_a} SUMMARY ---",
            f"Outgoing: {', '.join(self.send_a)} (${self.salary_out_a:,.0f})",
            f"Incoming: {', '.join(self.send_b)} (${self.salary_in_a:,.0f})",
            f"Payroll Shift: ${self.delta_a.pre_payroll:,.0f} -> ${self.delta_a.post_payroll:,.0f} ({self.delta_a.bracket_transition})",
            f"Friction Drag Relief: ${self.delta_a.friction_relief:+,.0f}",
            f"Net Surplus Swing (Delta NSV): ${self.delta_a.delta_nsv:+,.0f}",
            "",
            f"--- {self.team_b} SUMMARY ---",
            f"Outgoing: {', '.join(self.send_b)} (${self.salary_out_b:,.0f})",
            f"Incoming: {', '.join(self.send_a)} (${self.salary_in_b:,.0f})",
            f"Payroll Shift: ${self.delta_b.pre_payroll:,.0f} -> ${self.delta_b.post_payroll:,.0f} ({self.delta_b.bracket_transition})",
            f"Friction Drag Relief: ${self.delta_b.friction_relief:+,.0f}",
            f"Net Surplus Swing (Delta NSV): ${self.delta_b.delta_nsv:+,.0f}",
        ]

        if not self.is_legal:
            lines.append("")
            lines.append("--- CBA RULE VIOLATIONS ---")
            for idx, v in enumerate(self.violations, 1):
                lines.append(f"{idx}. {v}")

        lines.append("=" * 64)
        return "\n".join(lines)


def _resolve_players(
    identifiers: list[str],
    team_code: str,
    df_players: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Resolve player identifiers (ID or name) to player records for a specific team."""
    team_players = df_players[df_players["team"] == team_code].copy()
    resolved: list[dict[str, Any]] = []

    # Build lookup dictionaries
    id_map = {row["player_id"]: row.to_dict() for _, row in team_players.iterrows()}
    name_map = {_normalize_name_lookup(row["player_name"]): row.to_dict() for _, row in team_players.iterrows()}

    for ident in identifiers:
        clean_ident = ident.strip()
        norm_ident = _normalize_name_lookup(clean_ident)

        if clean_ident in id_map:
            resolved.append(id_map[clean_ident])
        elif norm_ident in name_map:
            resolved.append(name_map[norm_ident])
        else:
            # Check league-wide to give a helpful error message
            all_name_map = {
                _normalize_name_lookup(row["player_name"]): row["team"] for _, row in df_players.iterrows()
            }
            if norm_ident in all_name_map:
                actual_team = all_name_map[norm_ident]
                raise ValueError(
                    f"Player '{ident}' is on team '{actual_team}', not on '{team_code}'."
                )
            raise ValueError(f"Player '{ident}' not found in active 2025-26 roster records.")

    return resolved


def evaluate_trade(
    team_a: str,
    send_a: list[str],
    team_b: str,
    send_b: list[str],
    cash_a_to_b: float = 0.0,
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = "war_vorp",
    friction_lambda: dict[int, float] | None = None,
) -> TradeEvaluation:
    """Evaluate legality, apron restrictions, and Net Surplus swings for a proposed trade."""
    if df_players is None:
        df_players = pd.read_parquet(MASTER_PLAYERS_PARQUET)
    if df_teams is None:
        df_teams = pd.read_parquet(MASTER_TEAMS_PARQUET)

    norm_a = normalize_team(team_a)
    norm_b = normalize_team(team_b)

    if norm_a == norm_b:
        raise ValueError(f"Cannot trade within the same team ({norm_a}).")

    # Get team payroll records
    team_map = df_teams.set_index("team").to_dict(orient="index")
    if norm_a not in team_map:
        raise ValueError(f"Team '{norm_a}' not found in teams table.")
    if norm_b not in team_map:
        raise ValueError(f"Team '{norm_b}' not found in teams table.")

    payroll_a = float(team_map[norm_a]["total_payroll"])
    payroll_b = float(team_map[norm_b]["total_payroll"])

    # Resolve outgoing player records
    players_out_a = _resolve_players(send_a, norm_a, df_players)
    players_out_b = _resolve_players(send_b, norm_b, df_players)

    # Check for dead-money contracts
    has_dead_a = any(bool(p.get("is_dead_money", False)) for p in players_out_a)
    has_dead_b = any(bool(p.get("is_dead_money", False)) for p in players_out_b)

    contracts_out_a = [float(p["salary"]) for p in players_out_a]
    contracts_out_b = [float(p["salary"]) for p in players_out_b]

    salary_out_a = sum(contracts_out_a)
    salary_in_a = sum(contracts_out_b)

    salary_out_b = sum(contracts_out_b)
    salary_in_b = sum(contracts_out_a)

    # 1. Statutory Compliance Checks
    comp_a = check_trade_compliance(
        team_code=norm_a,
        pre_payroll=payroll_a,
        outgoing_contracts=contracts_out_a,
        incoming_contracts=contracts_out_b,
        outgoing_cash=cash_a_to_b,
        salary_cap=salary_cap,
        has_dead_money_outgoing=has_dead_a,
    )

    comp_b = check_trade_compliance(
        team_code=norm_b,
        pre_payroll=payroll_b,
        outgoing_contracts=contracts_out_b,
        incoming_contracts=contracts_out_a,
        outgoing_cash=0.0,
        salary_cap=salary_cap,
        has_dead_money_outgoing=has_dead_b,
    )

    all_violations = comp_a.violations + comp_b.violations
    is_legal = comp_a.is_compliant and comp_b.is_compliant

    # 2. Build Pre and Post Rosters
    full_roster_a = df_players[df_players["team"] == norm_a].to_dict(orient="records")
    full_roster_b = df_players[df_players["team"] == norm_b].to_dict(orient="records")

    ids_out_a = {p["player_id"] for p in players_out_a}
    ids_out_b = {p["player_id"] for p in players_out_b}

    post_roster_a = [p for p in full_roster_a if p["player_id"] not in ids_out_a] + players_out_b
    post_roster_b = [p for p in full_roster_b if p["player_id"] not in ids_out_b] + players_out_a

    post_payroll_a = payroll_a - salary_out_a + salary_in_a
    post_payroll_b = payroll_b - salary_out_b + salary_in_b

    # 3. Calculate Roster Delta Surplus Swings
    delta_a = calculate_roster_delta(
        team_code=norm_a,
        pre_roster=full_roster_a,
        post_roster=post_roster_a,
        pre_payroll=payroll_a,
        post_payroll=post_payroll_a,
        cost_per_win=cost_per_win,
        salary_cap=salary_cap,
        metric_col=metric_col,
        friction_lambda=friction_lambda,
    )

    delta_b = calculate_roster_delta(
        team_code=norm_b,
        pre_roster=full_roster_b,
        post_roster=post_roster_b,
        pre_payroll=payroll_b,
        post_payroll=post_payroll_b,
        cost_per_win=cost_per_win,
        salary_cap=salary_cap,
        metric_col=metric_col,
        friction_lambda=friction_lambda,
    )

    return TradeEvaluation(
        is_legal=is_legal,
        team_a=norm_a,
        team_b=norm_b,
        send_a=[p["player_name"] for p in players_out_a],
        send_b=[p["player_name"] for p in players_out_b],
        salary_out_a=round(salary_out_a, 2),
        salary_in_a=round(salary_in_a, 2),
        salary_out_b=round(salary_out_b, 2),
        salary_in_b=round(salary_in_b, 2),
        cash_a_to_b=round(cash_a_to_b, 2),
        compliance_a=comp_a,
        compliance_b=comp_b,
        delta_a=delta_a,
        delta_b=delta_b,
        violations=all_violations,
    )
