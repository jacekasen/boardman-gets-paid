"""Board Man Gets Paid: NBA Contract Valuation & Surplus Arbitrage Engine."""

from boardman.config import (
    DEFAULT_METRIC,
    DEFAULT_SEASON,
    SALARY_CAP_2025_26,
    LUXURY_TAX_2025_26,
    FIRST_APRON_2025_26,
    SECOND_APRON_2025_26,
)
from boardman.valuation import (
    DEFAULT_COST_PER_WIN,
    PlayerValuation,
    TeamValuation,
    build_league_surplus_board,
    calculate_player_valuation,
    calculate_roster_valuation,
)

__version__ = "0.2.0"
__all__ = [
    "PlayerValuation",
    "TeamValuation",
    "calculate_player_valuation",
    "calculate_roster_valuation",
    "build_league_surplus_board",
    "DEFAULT_COST_PER_WIN",
    "DEFAULT_METRIC",
    "DEFAULT_SEASON",
    "SALARY_CAP_2025_26",
    "LUXURY_TAX_2025_26",
    "FIRST_APRON_2025_26",
    "SECOND_APRON_2025_26",
]
