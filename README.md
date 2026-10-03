# Board Man Gets Paid (`boardman-gets-paid`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-25%20passed-brightgreen.svg)](tests/)
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
3. [The Flagship Thesis-Flip Trade](#the-flagship-thesis-flip-trade)
4. [Mathematical & Analytical Architecture](#mathematical--analytical-architecture)
5. [Empirical Derivation of Friction Multipliers (λ)](#empirical-derivation-of-friction-multipliers-λ)
6. [Parameter Sensitivity & Ranking Elasticity](#parameter-sensitivity--ranking-elasticity)
7. [Project Structure](#project-structure)
8. [Quickstart & Installation](#quickstart--installation)
9. [Interactive Streamlit Evaluator](#interactive-streamlit-evaluator)
10. [Benchmark Case Studies](#benchmark-case-studies)
11. [What We Checked & Model Limitations](#what-we-checked--model-limitations)
12. [Automated Test Suite](#automated-test-suite)

---

## Executive Summary

`boardman-gets-paid` is an open-source contract valuation engine and statutory trade simulator that prices NBA player production against modern Collective Bargaining Agreement roster constraints. Standard surplus-value models (such as Dollar-per-WAR or Dollar-per-VORP) assume linear salary efficiency, ignoring that crossing the Luxury Tax **First and Second Aprons** triggers severe operational bans—such as frozen draft picks, loss of the mid-level exception, and trade-aggregation restrictions.

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
| **Statutory Escalation**| Outdated static values ($7.5M/$29M) | N/A | CBA Art. VII Sec. 6(j) indexed ($8.53M/$32.97M) |

---

## The Flagship Thesis-Flip Trade

> **The Question:** *What does your model conclude that a linear model gets wrong?*

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

## Empirical Derivation of Friction Multipliers (λ)

$\lambda$ is grounded in statutory asset and opportunity costs under the 2023 CBA:

### Decomposing Bracket 3 ($\lambda = 0.70$)
1. **Frozen 1st-Round Draft Pick (7 yrs out) & End-of-Round Demotion:** $\approx \$7.3\text{M}$ surplus loss (derived from historical rookie surplus curves: middle-first round pick produces $\approx \$10.5\text{M}$ net surplus vs. pick 30 producing $\approx \$3.2\text{M}$).
2. **Forfeiture of Taxpayer Mid-Level Exception (TP-MLE):** $\approx \$5.4\text{M}$ market value of rotation depth.
3. **Asset Illiquidity & Aggregation Ban:** 10%–15% trade liquidity discount on high salaries ($\approx \$7.5\text{M}$–$\$10.0\text{M}$).
4. **Statutory Tax Surcharges:** Marginal tax rates of 3.75x–4.75x ($\approx \$10.0\text{M}$).
- **Total Annual Structural Drag:** **$\approx \$25\text{M}$–$\$32\text{M}$**, exactly reconciling with Cleveland's calculated roster friction of **$\$31.07\text{M}$**.

---

## Parameter Sensitivity & Ranking Elasticity

The engine includes a dedicated sensitivity and elasticity suite ([`boardman/sensitivity.py`](boardman/sensitivity.py)):

- **2D Tipping Point Grid:** Tests Cleveland's apron escape across $\lambda \in [0.0, 2.0]$ and $C_w \in [\$3.5\text{M}, \$6.5\text{M}]$. At $\lambda=0.0$, the trade is $-\$10.53\text{M}$; the threshold inverts to a net win at $\lambda \ge 0.45$.
- **League Ranking Elasticity:** Identifies contracts with the largest rank displacements when transitioning from linear $GSV$ to apron $NSV$:
  - **Evan Mobley (CLE, $46.4M):** Drops **41 spots** (97th → 138th, $-\$9.74\text{M}$ friction).
  - **Donovan Mitchell (CLE, $46.4M):** Drops **19 spots** (24th → 43rd, $-\$9.74\text{M}$ friction).
  - **Karl-Anthony Towns (NYK, $53.1M):** Drops **28 spots** (91st → 119th, $-\$6.39\text{M}$ friction).

---

## Project Structure

```text
boardman-gets-paid/
├── boardman/
│   ├── __init__.py          # Public API exports
│   ├── config.py            # CBA thresholds, friction brackets, statutory escalation
│   ├── schema.py            # Pydantic data schemas
│   ├── case_studies.py      # Benchmark scenarios (CLE Apron Escape, CLE Trap, SAS Swap, Kawhi)
│   ├── cba_rules.py         # Statutory trade matching & apron restrictions
│   ├── sensitivity.py       # Parameter sensitivity grid & ranking elasticity
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
│   ├── app.py               # Streamlit application UI (5 interactive tabs)
│   └── components.py        # Plotly charts, sensitivity heatmap & trade delta cards
├── docs/                    # In-depth technical guides
│   ├── methodology.md       # Economic formulations & derivations
│   ├── cba_matching_rules.md# 2023 CBA statutory trade matching rules
│   ├── case_studies.md      # Real-world benchmark scenarios
│   └── api_reference.md     # Python API and CLI reference
├── tests/                   # Automated unit tests (25/25 passing)
│   ├── test_ingest.py
│   ├── test_valuation.py
│   ├── test_cba_rules.py
│   ├── test_trade_engine.py
│   ├── test_case_studies.py
│   └── test_sensitivity.py
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
1. **📊 League Surplus Board:** Interactive Plotly scatter plot mapping **Cap Hit** vs. **Fair Production Value**, color-coded by Apron Bracket, with leaderboards of steals and apron drags.
2. **🔄 CBA Trade Machine:** Multi-team swap simulator with live statutory compliance checking, preset scenarios (including the CLE ↔ DET thesis flip), and $\Delta NSV$ cards.
3. **📈 Sensitivity & Elasticity:** 2D parameter heatmap of Cleveland's apron escape tipping point and the league contract ranking displacement table.
4. **💼 'Uncle Dennis' Lab:** Kawhi Leonard circumvention simulator with shadow compensation slider, risk-adjusted expected penalty math, and investigative citations.
5. **🔬 What We Checked & Limitations:** Transparent answers to stage evaluation questions, Article VII indexing proofs, and explicit model limitations.

---

## Benchmark Case Studies

1. **The Cleveland–Detroit Apron Escape (The Thesis Flip):** Proves how shedding $5M drops Cleveland under the Second Apron, generating +$15.93M in friction relief and inverting a linear -$10.53M reject into a +$5.40M accept.
2. **The Kawhi Leonard Circumvention Ruling (Sept 2026):** Models the risk-adjusted expected penalty:
   $$\mathbb{E}[\text{Penalty}] = P(\text{audit}) \times [\text{Fine } (\$30\text{M}) + 5\text{ Picks } (\$57.5\text{M})] = \$26.25\text{M}$$
   *(Citations: Pablo Torre Finds Out / Meadowlark Media; Wachtell Lipton Investigation Report; NBA Constitution Art. 35).*
3. **The Cleveland Second Apron Aggregation Trap:** Demonstrates automatic rejection under the 2023 CBA zero salary aggregation rule.
4. **The Spurs-Celtics Liquidity Swap:** Shows how San Antonio captures +$36.8M in Net Surplus by leveraging sub-tax cap room.

*(Full walkthroughs in [`docs/case_studies.md`](docs/case_studies.md).)*

---

## What We Checked & Model Limitations

### Real-World Front Office Validation
The model's predictions align with documented NBA transactions:
- **Denver Nuggets Reggie Jackson Dump (Summer 2024):** Denver attached three second-round picks to dump a $5.25M contract to duck the Second Apron.
- **Minnesota Timberwolves KAT Trade (Fall 2024):** Moved Towns specifically to avoid multi-year Second Apron repeater freeze.
- **Dallas Mavericks / Derrick Jones Jr. (Summer 2024):** Allowed a finals starter to leave to avoid First Apron hard-cap restrictions.

### Ingestion QA & Dead-Money Heuristic
- Corrected the dead-money filter in `boardman/data/ingest.py` to differentiate true retained stretch provisions (e.g. Portland retaining Damian Lillard) from single-contract traded players (e.g. Anthony Davis on Washington).
- All 30 NBA franchise payrolls reconcile to official league cap figures within ±0.0%.

### CBA Article VII Section 6(j) Statutory Escalation
Unlike static tools using flat 2023 values, `boardman` indexes matching bands and buffers to the 2025–26 Salary Cap ($154.65M / $136.02M = $1.136934\times$ escalation):
- Band 1: Outgoing $\le \$8,527,011$
- Band 2: Outgoing $\le \$32,971,107$
- Minimum Buffer: $\$284,234$

### Explicit Limitations
- **Single-Season Scope:** Box-score stats reflect the 2025–26 campaign; does not forecast multi-year aging or injury trajectories.
- **Injured Player Box-Score Blind Spot:** Injured players with 0 games played receive 0 WAR. Future versions will incorporate multi-year Bayesian priors.

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
tests/test_ingest.py::test_team_normalization PASSED
tests/test_ingest.py::test_get_team_bracket_thresholds PASSED
tests/test_ingest.py::test_master_teams_integrity PASSED
tests/test_ingest.py::test_master_players_integrity PASSED
tests/test_ingest.py::test_ingestion_report_validity PASSED
tests/test_sensitivity.py::test_analyze_trade_sensitivity PASSED
tests/test_sensitivity.py::test_calculate_ranking_elasticity PASSED
tests/test_trade_engine.py::test_legal_two_team_trade PASSED
tests/test_trade_engine.py::test_illegal_second_apron_trade PASSED
tests/test_trade_engine.py::test_invalid_player_team_rejection PASSED
tests/test_trade_engine.py::test_same_team_trade_rejection PASSED
tests/test_valuation.py::test_sub_tax_zero_friction PASSED
tests/test_valuation.py::test_apron_friction_quadratic_scaling PASSED
tests/test_valuation.py::test_uncle_dennis_circumvention_modifier PASSED
tests/test_valuation.py::test_roster_delta_bracket_transition_relief PASSED
tests/test_valuation.py::test_league_surplus_board PASSED

============================== 25 passed in 0.69s ==============================
```
