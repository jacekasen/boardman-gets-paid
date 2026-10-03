# Python API Reference & CLI Documentation

`boardman-gets-paid` exposes a typed Python API for contract valuation, surplus-value calculation, and ROI efficiency analysis.

---

## 1. Quick Import

```python
from boardman import (
    calculate_player_valuation,
    calculate_roster_valuation,
    calculate_roster_delta,
    build_league_surplus_board,
    DEFAULT_COST_PER_WIN,
    PlayerValuation,
    TeamValuation,
    RosterDelta,
)
```

---

## 2. Core Valuation Functions

### `calculate_player_valuation`
```python
def calculate_player_valuation(
    player: dict[str, Any] | BaseModel,
    team_payroll: float,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = DEFAULT_METRIC,
    uncle_dennis_cash: float = 0.0,
    friction_lambda: dict[int, float] | None = None,
) -> PlayerValuation
```
Calculates Fair Production Value, Gross Surplus, Apron Friction Tax, Net Surplus, and ROI Efficiency Multiple for an individual player contract.

- **Parameters:**
  - `player` *(dict | BaseModel)*: Player record containing `salary`, `war_projected` (or other metric), `is_dead_money`, `is_salary_known`, and `contract_tier`.
  - `team_payroll` *(float)*: Current committed team payroll in USD.
  - `cost_per_win` *(float)*: Open-market cost per win (default: $5,193,442.76).
  - `salary_cap` *(float)*: Season salary cap threshold (default: $154,647,000).
  - `metric_col` *(str)*: Metric to evaluate (default: `'war_projected'`).
- **Returns:** [`PlayerValuation`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/valuation.py#L23) object.

---

### `calculate_roster_valuation`
```python
def calculate_roster_valuation(
    players: list[dict[str, Any] | BaseModel],
    team_payroll: float | None = None,
    team_code: str = "TEAM",
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    metric_col: str = DEFAULT_METRIC,
    friction_lambda: dict[int, float] | None = None,
) -> TeamValuation
```
Aggregates contract valuations across an entire roster, computing total payroll, total production value, aggregate apron friction, and team net surplus.

- **Returns:** [`TeamValuation`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/valuation.py#L43) object.

---

### `build_league_surplus_board`
```python
def build_league_surplus_board(
    df_players: pd.DataFrame | None = None,
    df_teams: pd.DataFrame | None = None,
    metric_col: str = DEFAULT_METRIC,
    cost_per_win: float = DEFAULT_COST_PER_WIN,
    salary_cap: float = SALARY_CAP_2025_26,
    friction_lambda: dict[int, float] | None = None,
) -> pd.DataFrame
```
Generates the complete league-wide surplus leaderboard, ordered by `net_surplus` descending, with full contract tiers and ROI multiples.

---

## 3. Data Ingestion CLI

Run the full end-to-end data pipeline from local packaged raw inputs:

```bash
# Ingest 2025-26 data from packaged raw data
python -m boardman.data.ingest

# Ingest a specific season
python -m boardman.data.ingest --season 2025-26
```

Outputs generated:
- `data/processed/master_players_2025_26.parquet`
- `data/processed/master_players_2025_26.csv`
- `data/processed/master_teams_2025_26.parquet`
- `data/processed/master_teams_2025_26.csv`
- `data/processed/ingestion_report.json`

---

## 4. Web Snapshot CLI

Generate the static JSON payload consumed by the Next.js frontend:

```bash
python -m boardman.web_api snapshot > frontend/src/data/league.json
```
Or via the frontend convenience script:
```bash
npm run --prefix frontend data:refresh
```
