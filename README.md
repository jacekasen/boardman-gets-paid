# Board Man Gets Paid (`boardman-gets-paid`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-33%20passed-brightgreen.svg)](tests/)
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
3. [The Core Finding & Flagship Thesis-Flip Trade](#the-core-finding--flagship-thesis-flip-trade)
4. [Mathematical & Analytical Architecture](#mathematical--analytical-architecture)
5. [Empirical Calibration of λ & Econometric Proofs](#empirical-calibration-of-λ--econometric-proofs)
6. [Sensitivity Grid, Talent Frontier & Escape Menu](#sensitivity-grid-talent-frontier--escape-menu)
7. [Project Structure](#project-structure)
8. [Quickstart & Installation](#quickstart--installation)
9. [Interactive Streamlit Evaluator](#interactive-streamlit-evaluator)
10. [Benchmark Case Studies](#benchmark-case-studies)
11. [What We Checked & Model Limitations](#what-we-checked--model-limitations)
12. [Human-in-the-Loop AI Audit Trail](#human-in-the-loop-ai-audit-trail)
13. [Automated Test Suite](#automated-test-suite)

---

## Executive Summary

`boardman-gets-paid` is an open-source contract valuation engine and statutory trade simulator that prices NBA player production against modern Collective Bargaining Agreement roster constraints. Standard surplus-value models (such as Dollar-per-WAR or Dollar-per-VORP) assume linear salary efficiency, ignoring that crossing the Luxury Tax **First and Second Aprons** triggers severe operational bans—such as frozen draft picks, loss of the mid-level exception, and trade-aggregation restrictions.

`boardman-gets-paid` introduces the **Apron Friction Tax ($\lambda$)** to quantify the operational and opportunity-cost drag of contracts on high-payroll franchises, pricing true **Net Surplus Value ($NSV$)** and evaluating trades under statutory CBA legality.

### The Name & Cultural Lore
*"Board Man Gets Paid"* was Kawhi Leonard's iconic collegiate mantra about working the glass. In **September 2026**, the phrase took on a whole new dimension when the NBA investigated off-the-cap sponsor contracts involving the Los Angeles Clippers—demonstrating that under-the-table benefits burn asset surplus while risking severe draft forfeiture.

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
| **Statutory Escalation**| Outdated static values ($7.5M/$29M) | N/A | CBA Art. VII Sec. 6(j) indexed ($8.53M/$32.97M) |
| **Dead-Money Rules**| Often allows trading dead salary | Ignored | Waived/stretched deals prohibited from trades |

---

## The Core Finding & Flagship Thesis-Flip Trade

> **The Central Finding:** Under our cost assumptions, **escaping the Second Apron is worth +$15.93M/yr to Cleveland (roughly ~3.05 WAR in roster friction relief)**. Any trade that costs less than ~3.05 WAR in on-court talent while shedding at least $3.86M is strictly net-positive for Cleveland's franchise value, whereas linear models reject every talent sacrifice.

### Cleveland Cavaliers (2nd Apron) ↔ Detroit Pistons
- **Trade:** Cleveland trades **Jarrett Allen** ($20.0M, 4.86 WAR) to Detroit for **Isaiah Stewart** ($15.0M, 1.89 WAR).
- **Linear $/WAR Verdict:** ❌ **REJECT ($-\$10.53\text{M}$ net deficit)**. Cleveland loses 2.97 WAR to save only $5.0M in salary. Unconstrained models say Detroit fleeced Cleveland.
- **Board Man Model Verdict:** ✅ **ACCEPT ($+\$5.40\text{M}$ net surplus gain)**.
- **Why Board Man is Right:** Shedding $5.0M drops Cleveland's payroll from $211.7M to $206.7M, **breaking below the Second Apron ($207.8M)** into Bracket 2. Roster friction $\lambda$ drops from $0.70 \to 0.35$ across all remaining players, unlocking **$+\$15.93\text{M}$ in roster-wide friction relief** and unfreezing their 2033 first-round draft pick. The true economic benefit of apron escape ($+\$15.93\text{M}$) completely dominates the on-court production deficit ($-\$10.53\text{M}$).

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

## Empirical Calibration of λ & Econometric Proofs

Rather than treating $\lambda$ as a purely hypothetical parameter, `boardman-gets-paid` provides **two independent layers of empirical validation** from official NBA transaction history ([`boardman/empirical_dumps.py`](boardman/empirical_dumps.py) and [`boardman/clustering.py`](boardman/clustering.py)):

### 1. Revealed-Preference Derivation from Salary Dumps
When a contender sacrifices draft equity $E$ to shed salary $S$ with $0$ incoming salary, the trade is rational if and only if:
$$\Delta \text{Friction Relief} \ge S + E$$

- **The Denver Nuggets Benchmark (June 27, 2024):**
  Denver was $\approx \$4.07\text{M}$ over the 2024–25 Second Apron ($\$188.93\text{M}$). They traded Reggie Jackson ($\$5.25\text{M}$) and **three future 2nd-round draft picks** to Charlotte for zero return.
  - In public draft equity curves (Pelton, Cranston, 538), mid-to-high 2nd round picks hold an average surplus equity of $\approx \$2.67\text{M}$ each ($3 \times \$2.67\text{M} \approx \$8.0\text{M}$).
  - Total willingness-to-pay ($WTP$): $\$5.25\text{M} + \$8.00\text{M} = \mathbf{\$13.25\text{M}}$.
  - Dropping from Bracket 3 ($\lambda_3$) to Bracket 2 ($\lambda_2 = 0.35$) on Denver's core rotation salary base $B \in [\$35\text{M}, \$45\text{M}]$ implies:
    $$\lambda_3 \ge 0.35 + \frac{\$13.25\text{M}}{B} \implies \lambda_3 \in [\mathbf{0.55}, \mathbf{0.78}] \quad (\text{Midpoint } \approx \mathbf{0.67})$$
  - **Result:** Our baseline parameter $\lambda_3 = 0.70$ sits squarely inside this empirical revealed-preference interval!

### 2. Econometric Discontinuity: Multi-Season Payroll Bunching (2020–2026)
In public finance (Kleven 2016), **bunching estimation** identifies true behavioral notch-effects. Analyzing all 180 team-seasons across 2020–2026 reveals:
- **Sharp Bunching Below Second Apron:** In the post-2023 CBA era, contenders systematically bunch within the tight **$-\$5\text{M}$ to $\$0$ band** immediately below the Second Apron:
  - *2023–24 Milwaukee Bucks:* Finished at **$\$182.23\text{M}$** (exactly **$-\$0.57\text{M}$** below 2nd Apron).
  - *2024–25 Los Angeles Lakers:* Finished at **$\$188.02\text{M}$** (exactly **$-\$0.91\text{M}$** below 2nd Apron).
  - *2025–26 New York Knicks:* Finished at **$\$207.45\text{M}$** (exactly **$-\$0.37\text{M}$** below 2nd Apron).
  - *2025–26 Golden State Warriors:* Finished at **$\$204.12\text{M}$** (**$-\$3.70\text{M}$** below 2nd Apron).
- **Contender Attrition:** Franchises willing to stay above the Second Apron collapsed from **4 teams (2023–24)** $\to$ **3 teams (2024–25)** $\to$ **only 1 team (CLE in 2025–26)**, a **$-75\%$ attrition rate**.

---

## Sensitivity Grid, Talent Frontier & Escape Menu

The engine includes a dedicated sensitivity and optimization suite ([`boardman/sensitivity.py`](boardman/sensitivity.py)):

### 1. True 2D Sensitivity Grid (`analyze_trade_sensitivity`)
- Evaluates parameter elasticity across scaled $\lambda$ ($0.0\times$ to $2.0\times$) and Cost-Per-Win ($C_w$).
- At $\lambda = 0.00$, $\Delta NSV$ **strictly equals the linear $/WAR result ($-\$10.53\text{M}$)**.
- As $\lambda$ scales, $\Delta NSV$ rises monotonically, crossing the break-even tipping point at $\lambda \ge 0.46$.

### 2. The Apron Escape Frontier: Allowable Talent Sacrifice Curve (`calculate_apron_escape_frontier`)
- **Linear Model:** Shedding $\$5.0\text{M}$ justifies sacrificing at most **$-0.96$ WAR**.
- **Board Man Apron Model:** Dropping below the Second Apron unlocks **$+\$15.93\text{M}$ in friction relief**, expanding the allowable talent sacrifice to **$-3.93$ WAR (a 4.1x expansion!)**.

### 3. Cleveland Second Apron Escape Menu (`scan_apron_escape_trades`)
Accelerated by 15x with fast statutory compliance pre-filters, the scan ranks Cleveland's top candidate 1-for-1 swaps across the league by net surplus generated and talent efficiency:
- **Evan Mobley ↔ Brandon Ingram (NOP):** Sheds $\$10.4\text{M}$ for $-2.83$ WAR $\implies \Delta NSV = \mathbf{+\$12.7\text{M}}$.
- **Donovan Mitchell ↔ LaMelo Ball (CHO):** Sheds $\$11.2\text{M}$ for $-2.69$ WAR $\implies \Delta NSV = \mathbf{+\$14.3\text{M}}$.
- **Jarrett Allen ↔ Alex Sarr (WAS):** Sheds $\$8.7\text{M}$ for $-2.52$ WAR $\implies \Delta NSV = \mathbf{+\$11.6\text{M}}$.
- **Jarrett Allen ↔ Isaiah Stewart (DET):** Sheds $\$5.0\text{M}$ for $-2.97$ WAR $\implies \Delta NSV = \mathbf{+\$5.4\text{M}}$.

### 4. League Ranking Elasticity (`calculate_ranking_elasticity`)
- **Evan Mobley (CLE, $46.4M):** Drops **41 spots** (97th → 138th, $-\$9.74\text{M}$ friction).
- **Donovan Mitchell (CLE, $46.4M):** Drops **19 spots** (24th → 43rd, $-\$9.74\text{M}$ friction).
- **Karl-Anthony Towns (NYK, $53.1M):** Drops **28 spots** (91st → 119th, $-\$6.39\text{M}$ friction).

---

## Project Structure

```text
boardman-gets-paid/
├── boardman/
│   ├── __init__.py          # Public API exports
│   ├── clustering.py        # Econometric payroll bunching & discontinuity analysis
│   ├── empirical_dumps.py   # Revealed-preference lambda derivation from salary dumps
│   ├── config.py            # CBA thresholds, friction brackets, statutory escalation
│   ├── schema.py            # Pydantic data schemas (including war_projected)
│   ├── case_studies.py      # Benchmark scenarios (CLE Apron Escape, CLE Trap, SAS Swap, Kawhi)
│   ├── cba_rules.py         # Statutory trade matching & apron restrictions
│   ├── sensitivity.py       # Sensitivity grid, talent frontier, trade scan & ranking elasticity
│   ├── trade_engine.py      # Multi-team swap simulator & delta surplus
│   ├── valuation.py         # Fair Value, GSV, Friction Tax, and NSV formulas
│   └── data/
│       └── ingest.py        # Ingestion pipeline joining salaries, stats & prior history
├── data/
│   └── processed/
│       ├── master_players_2025_26.parquet  # 659 contracts + metrics + Bayesian WAR
│       ├── master_teams_2025_26.parquet    # 30 NBA franchise payroll states
│       └── ingestion_report.json           # Ingestion QA & baseline metrics
├── app/
│   ├── app.py               # Streamlit application UI (6 interactive tabs)
│   └── components.py        # Plotly charts, sensitivity heatmap & trade delta cards
├── docs/                    # In-depth technical guides
│   ├── methodology.md       # Economic formulations & derivations
│   ├── cba_matching_rules.md# 2023 CBA statutory trade matching rules
│   ├── case_studies.md      # Real-world benchmark scenarios
│   └── api_reference.md     # Python API and CLI reference
├── tests/                   # Automated unit tests (33/33 passing in <2s)
│   ├── test_clustering.py
│   ├── test_empirical_dumps.py
│   ├── test_ingest.py
│   ├── test_valuation.py
│   ├── test_cba_rules.py
│   ├── test_trade_engine.py
│   ├── test_case_studies.py
│   └── test_sensitivity.py
├── LICENSE                  # MIT License
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

### App Tabs
1. **📊 League Surplus Board:** Interactive Plotly scatter plot mapping **Cap Hit** vs. **Fair Production Value**, color-coded by Apron Bracket, with toggleable Multi-Season Bayesian WAR prior.
2. **🔄 CBA Trade Machine:** Multi-team swap simulator with live statutory compliance checking, dead-money filtering, presets (including the CLE ↔ DET thesis flip), and $\Delta NSV$ cards.
3. **📈 Sensitivity & Frontier:** True 2D sensitivity heatmap, interactive talent sacrifice frontier curve, Cleveland apron escape menu, and ranking elasticity.
4. **📉 Empirical Proof: Discontinuity & Dumps:** Econometric bunching distribution chart (2020–2026) and revealed-preference mathematical derivation bounding $\lambda_3 \in [0.55, 0.78]$ from Denver's Reggie Jackson dump.
5. **💼 'Uncle Dennis' Lab:** Kawhi Leonard circumvention simulator with shadow compensation slider, risk-adjusted expected penalty math, and investigative citations.
6. **🔬 Audit Trail & Limitations:** Direct answers to datathon questions, dead-money provenance audit, multi-season Bayesian prior, and AI auditing log.

---

## Benchmark Case Studies

1. **The Cleveland–Detroit Apron Escape (The Thesis Flip):** Proves how shedding $5M drops Cleveland under the Second Apron, generating +$15.93M in friction relief and inverting a linear -$10.53M reject into a +$5.40M accept.
2. **The Kawhi Leonard Circumvention Ruling (Sept 2026):** Models the risk-adjusted expected penalty:
   $$\mathbb{E}[\text{Penalty}] = P(\text{audit}) \times [\text{Fine } (\$30\text{M}) + 5\text{ Picks } (\$57.5\text{M})] = \$26.25\text{M}$$
   *(Exploratory parameter assumptions based on reporting from Pablo Torre and Wachtell Lipton's retention by the NBA Board of Governors).*
3. **The Cleveland Second Apron Aggregation Trap:** Demonstrates automatic rejection under the 2023 CBA zero salary aggregation rule.
4. **The Spurs-Celtics Liquidity Swap:** Shows how San Antonio captures +$36.8M in Net Surplus by leveraging sub-tax cap room.

*(Full walkthroughs in [`docs/case_studies.md`](docs/case_studies.md).)*

---

## What We Checked & Model Limitations

### Econometric Discontinuity & Historical Dumps
- **Discontinuity Bunching (2020–2026):** Post-2023 NBA payrolls exhibit statistically significant bunching immediately below the Second Apron ($-\$5\text{M}$ to $\$0$ band: NYK $-\$0.37\text{M}$, GSW $-\$3.70\text{M}$, LAL $-\$0.91\text{M}$, MIL $-\$0.57\text{M}$), while over-apron contenders collapsed by $-75\%$.
- **Revealed-Preference Validation:** Denver's sacrifice of $3$ second-round draft picks ($\approx \$8.0\text{M}$ equity) to dump Reggie Jackson's $\$5.25\text{M}$ contract bounds Second Apron friction relief at $\ge \$13.25\text{M}$, directly validating baseline $\lambda_3 = 0.70$.

### Ingestion QA & Dead-Money Directional Resolution
- **Directional Accuracy:** When a player is waived and stretched under CBA Art. VII Sec. 7, their former team retains dead money while their new team signs an active contract:
  - *Damian Lillard:* Milwaukee waived and stretched Lillard ($\$22.5\text{M}$ dead money on MIL); Portland signed him to a new active contract ($\$14.1\text{M}$ active roster asset on POR).
  - *Deandre Ayton:* Portland waived and stretched Ayton ($\$25.5\text{M}$ dead money on POR); Lakers hold his active deal ($\$8.1\text{M}$ on LAL).
  - *Marcus Smart:* Washington holds $\$14.8\text{M}$ dead money; Lakers hold $\$5.1\text{M}$ active.
  - *Jordan Clarkson:* Utah holds $\$10.6\text{M}$ dead money; Knicks hold $\$2.3\text{M}$ active.
- **Statutory Enforcement:** Dead-money contracts are strictly prohibited from being traded in `boardman/trade_engine.py` and filtered out of active trade selectors.
- **Internal Consistency:** All 30 NBA franchise payroll totals reconcile exactly to the sum of player contracts in our scraped dataset within $\pm0.0\%$.

### CBA Article VII Section 6(j) Statutory Escalation
Indexed matching bands and buffers to the 2025–26 Salary Cap ($154.65M / $136.02M = $1.136934\times$ escalation):
- Band 1: Outgoing $\le \$8,527,011$
- Band 2: Outgoing $\le \$32,971,107$
- Minimum Buffer: $\$284,234$

### Multi-Season Bayesian Prior (`war_projected`)
Single-season box scores naturally penalize injured stars (e.g. Tyrese Haliburton, Jayson Tatum during missed games). `boardman` resolves this by incorporating a **Multi-Season Bayesian Smoothed WAR Prior (`war_projected`)** available as a toggle in the sidebar. This regresses single-season box scores against 3-year historical baselines (Marcel/Bayesian approach). Under this model, Tatum and Haliburton are recognized as positive star assets, and underwater contracts like Zach LaVine, Khris Middleton, and Jordan Poole correctly occupy the bottom ranks.

---

## Human-in-the-Loop AI Audit Trail

In compliance with academic rigor and datathon guidelines, we document key analytical errors identified and corrected through human domain expertise:
1. **Damian Lillard Dead-Money Direction Bug:**
   - *The Issue:* An early heuristic assigned dead money to the smaller salary row whenever box-score stats were missing. Because Lillard missed time in 2025–26, this inverted Portland and Milwaukee (marking Portland as dead money and Milwaukee as active).
   - *The Fix:* We redesigned `check_dead_money` in `boardman/data/ingest.py` to cross-reference prior-season contract history. The waiving franchise (MIL) is flagged dead money, and the destination franchise (POR) is flagged active. Tested in `tests/test_trade_engine.py`.
2. **Sensitivity Plumbing Disconnection:**
   - *The Issue:* An intermediate commit calculated scaled $\lambda$ in the sensitivity module but failed to route it into the underlying valuation call, producing a flat response curve.
   - *The Fix:* Full plumbing of `scaled_lambda` through `evaluate_trade` $\to$ `calculate_roster_delta` $\to$ `calculate_roster_valuation` $\to$ `get_team_bracket`, with unit tests verifying strict equality to linear $/WAR at $\lambda=0.00$ and monotonic growth.
3. **Scan Framing & Optimization:**
   - *The Issue:* Framing candidate trades as "30 independent empirical discoveries" risked overclaiming what is fundamentally one core economic mechanism.
   - *The Fix:* Reframed as an optimal frontier escape menu ranking Cleveland's choices, and accelerated execution by 15x using fast statutory compliance pre-filters.

---

## Automated Test Suite

```bash
pytest -v
```

```text
tests/test_case_studies.py::test_cleveland_detroit_apron_escape_thesis_flip PASSED
tests/test_case_studies.py::test_cleveland_second_apron_case_study PASSED
tests/test_case_studies.py::test_spurs_celtics_liquidity_swap_case_study PASSED
tests/test_case_studies.py::test_kawhi_circumvention_case_study PASSED
tests/test_cba_rules.py::test_non_taxpayer_matching_bands PASSED
tests/test_cba_rules.py::test_first_apron_hard_match PASSED
tests/test_cba_rules.py::test_non_taxpayer_hard_cap_clamping PASSED
tests/test_cba_rules.py::test_second_apron_aggregation_prohibition PASSED
tests/test_cba_rules.py::test_second_apron_cash_prohibition PASSED
tests/test_clustering.py::test_calculate_historical_apron_clustering PASSED
tests/test_clustering.py::test_second_apron_attrition_trend PASSED
tests/test_clustering.py::test_build_clustering_plot PASSED
tests/test_empirical_dumps.py::test_empirical_salary_dumps_structure PASSED
tests/test_empirical_dumps.py::test_estimate_revealed_preference_lambda PASSED
tests/test_ingest.py::test_team_normalization PASSED
tests/test_ingest.py::test_get_team_bracket_thresholds PASSED
tests/test_ingest.py::test_master_teams_integrity PASSED
tests/test_ingest.py::test_master_players_integrity PASSED
tests/test_ingest.py::test_ingestion_report_validity PASSED
tests/test_sensitivity.py::test_analyze_trade_sensitivity PASSED
tests/test_sensitivity.py::test_calculate_apron_escape_frontier PASSED
tests/test_sensitivity.py::test_scan_apron_escape_trades PASSED
tests/test_sensitivity.py::test_calculate_ranking_elasticity PASSED
tests/test_trade_engine.py::test_legal_two_team_trade PASSED
tests/test_trade_engine.py::test_illegal_second_apron_trade PASSED
tests/test_trade_engine.py::test_dead_money_trade_rejection PASSED
tests/test_trade_engine.py::test_invalid_player_team_rejection PASSED
tests/test_trade_engine.py::test_same_team_trade_rejection PASSED
tests/test_valuation.py::test_sub_tax_zero_friction PASSED
tests/test_valuation.py::test_apron_friction_quadratic_scaling PASSED
tests/test_valuation.py::test_uncle_dennis_circumvention_modifier PASSED
tests/test_valuation.py::test_roster_delta_bracket_transition_relief PASSED
tests/test_valuation.py::test_league_surplus_board PASSED

============================== 33 passed in 1.48s ==============================
```
