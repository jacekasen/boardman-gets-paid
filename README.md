# Board Man Gets Paid (`boardman-gets-paid`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)](tests/)
[![CBA](https://img.shields.io/badge/CBA-2023%20Ruleset-orange.svg)](docs/cba_matching_rules.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Modern NBA Collective Bargaining Agreement (CBA) Roster Constraint, Apron Friction Tax & Net Surplus Valuation Engine.**

**Author:** Jace Kasen  
**Repository:** `~/dev/boardman-gets-paid`  
**Related Monorepo:** [`~/dev/nba`](file:///Users/jankasen/dev/nba)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [The Problem: Linear Valuation vs. Non-Linear CBA Drag](#the-problem-linear-valuation-vs-non-linear-cba-drag)
3. [Mathematical & Analytical Architecture](#mathematical--analytical-architecture)
4. [Project Structure](#project-structure)
5. [Quickstart & Installation](#quickstart--installation)
6. [Interactive Streamlit Evaluator](#interactive-streamlit-evaluator)
7. [Python Library Usage](#python-library-usage)
8. [Benchmark Case Studies](#benchmark-case-studies)
9. [Detailed Documentation Links](#detailed-documentation-links)
10. [Automated Test Suite](#automated-test-suite)

---

## Executive Summary

`boardman-gets-paid` is an open-source contract valuation engine and statutory trade simulator that prices NBA player production against modern Collective Bargaining Agreement roster constraints. Standard surplus-value models (such as Dollar-per-WAR or Dollar-per-VORP) assume linear salary efficiency, ignoring that crossing the Luxury Tax **First and Second Aprons** triggers operational bans—such as frozen draft picks, loss of the mid-level exception, and trade-aggregation restrictions.

`boardman-gets-paid` introduces the **Apron Friction Tax ($\lambda$)** to quantify the operational and opportunity-cost drag of contracts on high-payroll franchises, pricing true **Net Surplus Value ($NSV$)** and evaluating trades under statutory CBA legality.

### The Name & Cultural Lore
*"Board Man Gets Paid"* was Kawhi Leonard's iconic collegiate mantra about working the glass. In **September 2026**, the phrase took on a whole new dimension when the NBA concluded its historic salary cap circumvention investigation into the Los Angeles Clippers—issuing a **$30M fine**, stripping **5 consecutive first-round picks (2029–2033)**, and issuing executive suspensions over off-the-cap sponsor contracts. 

Whether on the cap sheet or off it, *Board Man Gets Paid*.

---

## The Problem: Linear Valuation vs. Non-Linear CBA Drag

| Dimension | Standard Tools (Fanspo, ESPN Trade Machine) | Traditional $/WAR Models | `boardman-gets-paid` |
| :--- | :--- | :--- | :--- |
| **Trade Legality** | Static binary checker | Ignored | Exact 2023 CBA rule engine |
| **Asset Valuation** | Raw AAV only | Flat linear $/Win | Non-linear Net Surplus ($NSV$) |
| **Apron Penalties** | Flagged as restriction | Ignored | Quadratic Friction Tax ($\lambda$) |
| **Context Sensitivity**| None | League-wide flat rate | Franchise-state dependent |
| **Roster Externalities**| None | None | Roster-wide friction relief ($\Delta NSV$) |

---

## Mathematical & Analytical Architecture

### 1. Public Metric Standardization
The engine standardizes publicly available box-score impact metrics (VORP and Win Shares) from Basketball-Reference:

$$\hat{W}_{\text{VORP}} = 2.70 \times \text{VORP}$$

$$\hat{W}_{\text{Blend}} = 0.5 \times (2.70 \times \text{VORP}) + 0.5 \times \text{WS}$$

### 2. Fair Production Value ($FV$) & Gross Surplus ($GSV$)
Calibrated against unconstrained open-market veterans ($C_w = \$5,229,871.98$ per win for 2025–26):

$$FV_i = \hat{W}_i \times C_w$$

$$GSV_i = FV_i - \text{Cap Hit}_i$$

### 3. Apron Friction Tax ($\lambda$)
Quantifies operational drag and asset illiquidity:

$$\text{Friction}_i = \lambda(T) \times \text{Cap Hit}_i \times \left(\frac{\text{Cap Hit}_i}{\text{Salary Cap}}\right)$$

$$NSV_i = GSV_i - \text{Friction}_i$$

Where $\lambda(T)$ is conditioned on the franchise's payroll bracket $T$:
- **Bracket 0 ($< \text{Tax}$):** $\lambda = 0.00$ *(Full roster mobility)*
- **Bracket 1 ($\text{Tax} \to \text{1st Apron}$):** $\lambda = 0.15$ *(Cash tax penalties)*
- **Bracket 2 ($\text{1st} \to \text{2nd Apron}$):** $\lambda = 0.35$ *(Hard 100% matching, loss of BAE)*
- **Bracket 3 ($> \text{2nd Apron}$):** $\lambda = 0.70$ *(Frozen picks, zero aggregation, zero cash)*

### 4. Trade Net Surplus Delta ($\Delta NSV_{\text{Team}}$)
Captures player talent changes plus the **roster-wide friction relief** when shedding payroll drops a team down an apron tier:

$$\Delta NSV_{\text{Team}} = \sum_{k \in \text{Roster}_{\text{post}}} NSV_k(T_{\text{post}}) - \sum_{k \in \text{Roster}_{\text{pre}}} NSV_k(T_{\text{pre}})$$

---

## Project Structure

```text
boardman-gets-paid/
├── boardman/
│   ├── __init__.py          # Public API exports
│   ├── config.py            # CBA thresholds, friction brackets, aliases
│   ├── schema.py            # Pydantic data schemas
│   ├── case_studies.py      # Benchmark scenarios (CLE Trap, SAS-BOS, Kawhi Lab)
│   ├── cba_rules.py         # Statutory trade matching & apron restrictions
│   ├── trade_engine.py      # Multi-team swap simulator & delta surplus
│   ├── valuation.py         # Fair Value, GSV, Friction Tax, and NSV formulas
│   └── data/
│       └── ingest.py        # Ingestion pipeline joining salaries & box-score stats
├── data/
│   └── processed/
│       ├── master_players_2025_26.parquet  # 659 contracts + metrics + WAR
│       ├── master_teams_2025_26.parquet    # 30 NBA franchise payroll states
│       └── ingestion_report.json           # Ingestion QA & baseline metrics
├── app/
│   ├── app.py               # Streamlit application UI
│   └── components.py        # Plotly charts & trade delta cards
├── docs/                    # In-depth technical guides
│   ├── methodology.md       # Economic formulations & derivations
│   ├── cba_matching_rules.md# 2023 CBA statutory trade matching rules
│   ├── case_studies.md      # Real-world benchmark scenarios
│   └── api_reference.md     # Python API and CLI reference
├── tests/                   # Automated unit tests (22/22 passing)
│   ├── test_ingest.py
│   ├── test_valuation.py
│   ├── test_cba_rules.py
│   ├── test_trade_engine.py
│   └── test_case_studies.py
├── pyproject.toml
└── requirements.txt
```

---

## Quickstart & Installation

1. Activate your conda environment (Python 3.10+):
   ```bash
   conda activate nba
   ```

2. Clone or navigate to the repository:
   ```bash
   cd ~/dev/boardman-gets-paid
   ```

3. Install the package in editable development mode:
   ```bash
   pip install -e ".[dev,ui]"
   ```

4. Run the automated test suite:
   ```bash
   pytest -v
   ```

---

## Interactive Streamlit Evaluator

Launch the web application:
```bash
streamlit run app/app.py
```
*Opens in your browser at `http://localhost:8501`.*

### App Features
- **📊 League Surplus Board:** Interactive Plotly scatter plot mapping **Cap Hit** vs. **Fair Production Value**, color-coded by Apron Bracket, with leaderboards of steals (Wembanyama, Jokić, SGA) and apron drags.
- **🔄 CBA Trade Machine:** Select Team A and Team B, multi-select players to trade, and inspect live statutory legality banners and $\Delta NSV$ cards.
- **💼 "Uncle Dennis" Circumvention Lab:** Inject off-the-cap sponsor compensation ($0 to $25M/yr) to visualize true surplus erosion under shadow financing.

---

## Python Library Usage

```python
from boardman import evaluate_trade, calculate_player_valuation

# 1. Evaluate a multi-player transaction
trade = evaluate_trade(
    team_a="SAS",
    send_a=["Harrison Barnes", "Kelly Olynyk"],
    team_b="BOS",
    send_b=["Derrick White"]
)

print(trade.summary())
# Outputs: Legality, post-trade payroll, bracket shift, and Delta NSV ($)

# 2. Evaluate an individual contract with off-cap cash
kawhi_val = calculate_player_valuation(
    player={"player_id": "leonaka01", "player_name": "Kawhi Leonard", "salary": 50_000_000, "war_vorp": 14.3},
    team_payroll=188_928_780,  # Bracket 1
    uncle_dennis_cash=7_000_000  # $7M Aspiration off-cap endorsement
)
print(f"Net Surplus: ${kawhi_val.net_surplus:+,.0f}")
```

---

## Benchmark Case Studies

1. **The Kawhi Leonard Circumvention Ruling (Sept 2026):** Models how adding $7M/year in shadow sponsor payments (Aspiration) burns real economic surplus while risking catastrophic draft forfeiture.
2. **The Cleveland Second Apron Aggregation Trap:** Demonstrates how Cleveland's $211.7M payroll (Bracket 3, $\lambda=0.70$) triggers automatic rejection under the Second Apron salary aggregation ban.
3. **The Spurs-Celtics Liquidity Swap:** Shows how San Antonio captures **+$36.8M in Net Surplus** by absorbing Derrick White into sub-tax cap room.

*(Full walkthroughs in [`docs/case_studies.md`](docs/case_studies.md).)*

---

## Detailed Documentation Links

- [📐 Valuation Methodology & Economics](docs/methodology.md): Full mathematical derivations and metric calibration.
- [⚖️ Statutory 2023 CBA Matching Rules](docs/cba_matching_rules.md): Band thresholds, hard-cap clamping, and apron bans.
- [🏀 Empirical Case Studies](docs/case_studies.md): Detailed breakdowns of real-world scenarios.
- [📚 Python API & CLI Reference](docs/api_reference.md): Complete function signatures and parameters.

---

## Automated Test Suite

The test suite covers data integrity, valuation mechanics, CBA statutory boundaries, and trade simulations:
```bash
pytest -v
```

```text
tests/test_case_studies.py::test_cleveland_second_apron_case_study PASSED
tests/test_case_studies.py::test_spurs_celtics_liquidity_swap_case_study PASSED
tests/test_case_studies.py::test_kawhi_circumvention_case_study PASSED
tests/test_cba_rules.py::test_non_taxpayer_matching_bands PASSED
tests/test_cba_rules.py::test_first_apron_hard_match PASSED
tests/test_cba_rules.py::test_non_taxpayer_hard_cap_clamping PASSED
tests/test_cba_rules.py::test_second_apron_aggregation_prohibition PASSED
tests/test_cba_rules.py::test_second_apron_cash_prohibition PASSED
tests/test_ingest.py::test_team_normalization PASSED
tests/test_ingest.py::test_get_team_bracket_thresholds PASSED
tests/test_ingest.py::test_master_teams_integrity PASSED
tests/test_ingest.py::test_master_players_integrity PASSED
tests/test_ingest.py::test_ingestion_report_validity PASSED
tests/test_trade_engine.py::test_legal_two_team_trade PASSED
tests/test_trade_engine.py::test_illegal_second_apron_trade PASSED
tests/test_trade_engine.py::test_invalid_player_team_rejection PASSED
tests/test_trade_engine.py::test_same_team_trade_rejection PASSED
tests/test_valuation.py::test_sub_tax_zero_friction PASSED
tests/test_valuation.py::test_apron_friction_quadratic_scaling PASSED
tests/test_valuation.py::test_uncle_dennis_circumvention_modifier PASSED
tests/test_valuation.py::test_roster_delta_bracket_transition_relief PASSED
tests/test_valuation.py::test_league_surplus_board PASSED

============================== 22 passed in 0.50s ==============================
```
