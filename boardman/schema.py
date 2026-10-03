"""Data models and validation schemas for players, contracts, and team payroll states."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlayerRecord(BaseModel):
    """Normalized player contract, box-score impact, and win metrics for a single season."""

    player_id: str = Field(description="Unique Basketball-Reference player slug, e.g. jokicni01")
    player_name: str = Field(description="Display player name")
    player_url: str = Field(description="Canonical Basketball-Reference profile URL")
    season: str = Field(default="2025-26", description="NBA season in YYYY-YY format")
    team: str = Field(description="Contract franchise abbreviation (e.g. DEN, BOS, NYK)")
    salary: float = Field(ge=0.0, description="Annual cap hit in USD")
    cap_share: float = Field(ge=0.0, description="Salary as a percentage of that season's salary cap")
    is_dead_money: bool = Field(default=False, description="Flagged true if waived/stretched dead salary allocation")
    is_injured_zero_minutes: bool = Field(default=False, description="Flagged true if player logged zero regular season minutes")
    games: int = Field(default=0, ge=0, description="Regular season games played")
    minutes: float = Field(default=0.0, ge=0.0, description="Total regular season minutes played")
    per: float | None = Field(default=None, description="Player Efficiency Rating")
    bpm: float | None = Field(default=None, description="Box Plus/Minus per 100 possessions")
    vorp: float = Field(default=0.0, description="Value Over Replacement Player")
    ws: float = Field(default=0.0, description="Total Win Shares")
    ws_per_48: float | None = Field(default=None, description="Win Shares per 48 minutes")
    war_vorp: float = Field(default=0.0, description="Wins Above Replacement calibrated as 2.70 * VORP")
    war_blend: float = Field(default=0.0, description="Blended Wins estimate: 0.5 * (2.70 * VORP) + 0.5 * WS")
    war_projected: float = Field(default=0.0, description="Bayesian smoothed multi-season projected WAR prior")


class TeamRecord(BaseModel):
    """Team payroll summary, threshold distances, and modern CBA apron bracket state."""

    team: str = Field(description="Standard franchise abbreviation")
    season: str = Field(default="2025-26", description="NBA season in YYYY-YY format")
    salary_cap: float = Field(gt=0.0, description="League salary cap threshold")
    luxury_tax: float = Field(gt=0.0, description="Luxury tax threshold")
    first_apron: float = Field(gt=0.0, description="First apron threshold")
    second_apron: float = Field(gt=0.0, description="Second apron threshold")
    total_payroll: float = Field(ge=0.0, description="Total committed team salary payroll in USD")
    total_cap_share: float = Field(ge=0.0, description="Team payroll as percentage of salary cap")
    distance_to_tax: float = Field(description="Payroll minus luxury tax line (positive = over tax)")
    distance_to_first_apron: float = Field(description="Payroll minus first apron line (positive = over 1st apron)")
    distance_to_second_apron: float = Field(description="Payroll minus second apron line (positive = over 2nd apron)")
    bracket: int = Field(ge=0, le=3, description="Apron bracket: 0 (sub-tax), 1 (tax), 2 (1st apron), 3 (2nd apron)")
    lambda_tax: float = Field(ge=0.0, le=1.0, description="Apron operational friction penalty multiplier")
    known_player_count: int = Field(ge=0, description="Count of roster players with known cap allocations")


class IngestionReport(BaseModel):
    """Summary QA statistics produced by the ingestion pipeline."""

    season: str
    total_salary_records: int
    players_with_known_salary: int
    players_with_stats: int
    players_zero_minutes: int
    total_teams: int
    teams_bracket_0_sub_tax: int
    teams_bracket_1_tax: int
    teams_bracket_2_first_apron: int
    teams_bracket_3_second_apron: int
    unconstrained_cost_per_win: float
