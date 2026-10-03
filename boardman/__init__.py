"""Board Man Gets Paid: Modern NBA CBA Roster Constraint & Apron Friction Valuation Engine."""

from boardman.case_studies import (
    run_cleveland_detroit_apron_escape,
    run_cleveland_second_apron_trap,
    run_kawhi_circumvention_case_study,
    run_spurs_celtics_liquidity_swap,
)
from boardman.sensitivity import (
    analyze_trade_sensitivity,
    calculate_ranking_elasticity,
)
from boardman.trade_engine import TradeEvaluation, evaluate_trade
from boardman.valuation import (
    PlayerValuation,
    RosterDelta,
    TeamValuation,
    build_league_surplus_board,
    calculate_player_valuation,
    calculate_roster_delta,
    calculate_roster_valuation,
)

__version__ = "0.1.0"
__all__ = [
    "evaluate_trade",
    "TradeEvaluation",
    "calculate_player_valuation",
    "calculate_roster_valuation",
    "calculate_roster_delta",
    "build_league_surplus_board",
    "analyze_trade_sensitivity",
    "calculate_ranking_elasticity",
    "run_cleveland_detroit_apron_escape",
    "run_cleveland_second_apron_trap",
    "run_spurs_celtics_liquidity_swap",
    "run_kawhi_circumvention_case_study",
    "PlayerValuation",
    "TeamValuation",
    "RosterDelta",
]
