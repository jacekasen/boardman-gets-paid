# Python API Reference & CLI Documentation

`boardman-gets-paid` exposes a typed Python API for contract valuation, CBA compliance checking, sensitivity analysis, and trade simulation.

---

## 1. Quick Import

```python
from boardman import (
    evaluate_trade,
    calculate_player_valuation,
    calculate_roster_valuation,
    calculate_roster_delta,
    build_league_surplus_board,
    analyze_trade_sensitivity,
    calculate_ranking_elasticity,
    TradeEvaluation,
    PlayerValuation,
    TeamValuation,
    RosterDelta,
)
```

---

## 2. Core Trade Functions

### `evaluate_trade`
```python
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
) -> TradeEvaluation
```
Simulates a transaction between two franchises, checking 2023 CBA statutory legality and calculating post-trade Net Surplus swings ($\Delta NSV$).

- **Parameters:**
  - `team_a` *(str)*: Team A code (e.g. `'SAS'`, `'BOS'`, `'CLE'`).
  - `send_a` *(list[str])*: Outgoing player identifiers from Team A (player ID or player name).
  - `team_b` *(str)*: Team B code.
  - `send_b` *(list[str])*: Outgoing player identifiers from Team B.
  - `cash_a_to_b` *(float)*: Outgoing cash from Team A to Team B (default `0.0`).
  - `metric_col` *(str)*: Metric to use (`'war_vorp'` or `'war_blend'`).
- **Returns:** [`TradeEvaluation`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/trade_engine.py#L34) object.

#### Example:
```python
trade = evaluate_trade(
    team_a="CLE",
    send_a=["Jarrett Allen"],
    team_b="DET",
    send_b=["Isaiah Stewart"]
)
print(trade.summary())
print(f"Is Legal: {trade.is_legal}")
print(f"CLE Delta NSV: ${trade.delta_a.delta_nsv:+,.0f}")
print(f"Friction Relief: ${trade.delta_a.friction_relief:+,.0f}")
```

---

## 3. Valuation Functions

### `calculate_player_valuation`
```python
def calculate_player_valuation(
    player: dict[str, Any] | BaseModel,
    team_payroll: float,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = "war_vorp",
    uncle_dennis_cash: float = 0.0,
) -> PlayerValuation
```
Calculates Fair Production Value, Gross Surplus, Apron Friction Tax, and Net Surplus for an individual player contract.

- **Parameters:**
  - `player` *(dict | BaseModel)*: Player record containing `salary`, `war_vorp` (or specified metric), etc.
  - `team_payroll` *(float)*: Current committed team payroll in USD.
  - `uncle_dennis_cash` *(float)*: Optional off-the-cap shadow compensation subsidy.
- **Returns:** [`PlayerValuation`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/valuation.py#L20).

---

### `calculate_roster_valuation`
```python
def calculate_roster_valuation(
    players: list[dict[str, Any] | BaseModel],
    team_payroll: float | None = None,
    team_code: str = "TEAM",
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = "war_vorp",
) -> TeamValuation
```
Aggregates production value, gross surplus, friction tax, and net surplus across a full roster.

- **Returns:** [`TeamValuation`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/valuation.py#L38).

---

### `calculate_roster_delta`
```python
def calculate_roster_delta(
    team_code: str,
    pre_roster: list[dict[str, Any] | BaseModel],
    post_roster: list[dict[str, Any] | BaseModel],
    pre_payroll: float | None = None,
    post_payroll: float | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = "war_vorp",
) -> RosterDelta
```
Calculates the Net Surplus swing ($\Delta NSV_{\text{Team}}$) resulting from a roster transition, including roster-wide friction drag relief.

- **Returns:** [`RosterDelta`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/valuation.py#L54).

---

### `build_league_surplus_board`
```python
def build_league_surplus_board(
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    metric_col: str = "war_vorp",
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
) -> pd.DataFrame
```
Generates a complete DataFrame of all active NBA contracts ranked by Net Surplus Value ($NSV$).

---

## 4. Parameter Sensitivity & Elasticity Functions

### `analyze_trade_sensitivity`
```python
def analyze_trade_sensitivity(
    team_a: str = "CLE",
    send_a: list[str] | None = None,
    team_b: str = "DET",
    send_b: list[str] | None = None,
    lambda_scales: list[float] | None = None,
    cost_per_win_range: list[float] | None = None,
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
) -> pd.DataFrame
```
Evaluates a trade's surplus swing across a 2D parameter grid of $\lambda$ scale ($0.0\times$ to $2.0\times$) and Cost-Per-Win ($C_w$), pinpointing the exact tipping point where apron friction inverts the transaction decision.

---

### `calculate_ranking_elasticity`
```python
def calculate_ranking_elasticity(
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
) -> pd.DataFrame
```
Measures contract ranking displacements between linear Gross Surplus ($GSV$) and apron-aware Net Surplus ($NSV$), highlighting the largest downward shifts caused by the Apron Friction Tax on high-payroll franchises.

---

## 5. CBA Statutory Rules Functions

### `check_trade_compliance`
```python
def check_trade_compliance(
    team_code: str,
    pre_payroll: float,
    outgoing_contracts: list[float],
    incoming_contracts: list[float],
    outgoing_cash: float = 0.0,
    salary_cap: float = SALARY_CAP_2025_26,
    first_apron: float = FIRST_APRON_2025_26,
    second_apron: float = SECOND_APRON_2025_26,
) -> TradeComplianceCheck
```
Validates matching bounds (escalated under CBA Art. VII Sec. 6(j)), First Apron hard-caps, Second Apron aggregation prohibitions, and cash limits for a single franchise.

---

## 6. Command-Line Interface (CLI) Usage

### Ingest & Rebuild Datasets
```bash
# Ingest 2025-26 data from local ~/dev/nba source
python -m boardman.data.ingest

# Target a specific season
python -m boardman.data.ingest --season 2025-26
```

### Launch Streamlit Dashboard
```bash
streamlit run app/app.py
```

### Run Unit Tests
```bash
pytest -v
```
