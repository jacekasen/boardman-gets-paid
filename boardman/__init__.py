"""Board Man Gets Paid: Modern NBA CBA Roster Constraint & Apron Friction Valuation Engine."""

from boardman.case_studies import (
    run_cleveland_dallas_strus_martin_escape,
    run_cleveland_detroit_apron_escape,
    run_cleveland_second_apron_trap,
    run_flagship_apron_escape_pair,
    run_kawhi_circumvention_case_study,
    run_spurs_celtics_liquidity_swap,
)
from boardman.config import (
    DEFAULT_METRIC,
    SECOND_APRON_COST_COMPONENTS,
)
from boardman.sensitivity import (
    analyze_trade_sensitivity,
    calculate_apron_escape_frontier,
    calculate_break_even_lambda_3,
    calculate_flagship_uncertainty_pair,
    calculate_headline_uncertainty,
    calculate_ranking_elasticity,
    scan_apron_escape_trades,
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
    "calculate_apron_escape_frontier",
    "calculate_break_even_lambda_3",
    "calculate_headline_uncertainty",
    "calculate_flagship_uncertainty_pair",
    "scan_apron_escape_trades",
    "calculate_ranking_elasticity",
    "run_cleveland_dallas_strus_martin_escape",
    "run_cleveland_detroit_apron_escape",
    "run_flagship_apron_escape_pair",
    "run_cleveland_second_apron_trap",
    "run_spurs_celtics_liquidity_swap",
    "run_kawhi_circumvention_case_study",
    "PlayerValuation",
    "TeamValuation",
    "RosterDelta",
    "DEFAULT_METRIC",
    "SECOND_APRON_COST_COMPONENTS",
]
