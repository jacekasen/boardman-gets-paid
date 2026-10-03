# Board Man Gets Paid (`boardman-gets-paid`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-36%20passed-brightgreen.svg)](tests/)

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
3. [The Core Finding & Flagship Conditional Trade](#the-core-finding--flagship-conditional-trade)
4. [Mathematical & Analytical Architecture](#mathematical--analytical-architecture)
5. [Empirical Tests of λ & Econometric Evidence](#empirical-tests-of-λ--econometric-evidence)
6. [Sensitivity Grid, Uncertainty Analysis & Escape Menu](#sensitivity-grid-uncertainty-analysis--escape-menu)
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

> **Temporal Scope:** All contracts, payroll states, and trade scenarios evaluate the **2025–26 NBA season** (with 2026–27 currently underway). Multi-season historical metrics are incorporated via a multi-season blended talent baseline prior (`war_projected`).


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

## The Core Finding: Flagship Pair of Results

Rather than pinning our findings to a single trade whose conclusion swings on injury assumptions, `boardman-gets-paid` presents a **Flagship Pair of Results** evaluated under the primary multi-season true-talent prior (`war_projected`):

### 1. 💎 Flagship 1: The Robust Apron Escape Flip (Cleveland ↔ Dallas)
- **The Trade:** Cleveland ($211.7M payroll, Bracket 3 / Second Apron) trades **Max Strus** ($15.94M, 1.10 WAR) to Dallas for **Caleb Martin** ($9.59M, -0.23 WAR).
- **Linear $/WAR Verdict:** ❌ **REJECT ($-\$613\text{K}$ net deficit)**. Cleveland sheds $\$6.34\text{M}$ in salary while sacrificing $1.33$ WAR, losing $\$613\text{K}$ in unconstrained on-court value.
- **Board Man Net Surplus Verdict:** ✅ **ACCEPT ($+\$15.29\text{M}$ Net Surplus Gain)**.
- **Mechanism:** Shedding $\$6.34\text{M}$ drops Cleveland's payroll to $\$205.3\text{M}$, **comfortably below the Second Apron of $\$207.8\text{M}$** into Bracket 2 ($\lambda = 0.35$). This unlocks **$+\$15.90\text{M}$ in roster-wide friction relief** and unfreezes Cleveland's 2033 first-round draft pick.
- **Robustness:** Because the linear deficit is only $\$613\text{K}$, break-even requires $\lambda_3 \ge 0.356$ (holding $\lambda_2 = 0.35$ fixed). This flip is net-positive in **100.0% of Monte Carlo scenarios** drawn from our 4 sourced statutory cost components!

### 2. ⚡ Flagship 2: The High-Stakes, Assumption-Dependent Flip (Cleveland ↔ Detroit)
- **The Trade:** Cleveland trades **Jarrett Allen** ($20.0M, 6.37 WAR) to Detroit for **Isaiah Stewart** ($15.0M, 1.70 WAR).
- **Linear $/WAR Verdict:** ❌ **REJECT ($-\$19.42\text{M}$ net deficit)**. Stewart represents a severe $4.67$ WAR drop under multi-season true-talent baselines.
- **Board Man Net Surplus Verdict (baseline $\lambda_3 = 0.70$):** ❌ **REJECT ($-\$3.49\text{M}$ deficit)**.
- **Insight:** Second Apron friction relief ($+\$15.93\text{M}$) cannot overcome a 4.67 WAR talent drop unless escaping is worth $\ge \$19.42\text{M}$/yr, requiring $\mathbf{\lambda_3 \ge 0.779}$. Only ~3-4% of draws from our sourced statutory cost components clear this threshold. This illustrates a high-stakes organizational gamble on extreme friction severity.
*(Note: Under single-season box scores where Allen missed time, the linear deficit was only -$10.53M and the trade flipped at $\lambda_3 \ge 0.58$. `boardman` transparently exposes this assumption sensitivity.)*

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

## Empirical Tests of λ & Econometric Evidence

$\lambda$ is a scenario input built from a statutory cost breakdown ([`boardman/config.py`](boardman/config.py)). We test it against NBA transaction history in two ways ([`boardman/empirical_dumps.py`](boardman/empirical_dumps.py) and [`boardman/clustering.py`](boardman/clustering.py)). Neither pins down $\lambda_3$; they show that teams respond to thresholds.

### 1. Can Salary Dumps Identify λ₃? (No)
When a contender sacrifices draft equity $E$ to shed salary $S$ with $0$ incoming salary, it saves $S$ in salary and $T_{\text{tax}}$ in luxury tax, and gives up $E$ plus any on-court production ($\Delta W \times C_w$). The trade is rational if and only if:
$$\Delta \text{Friction Relief} \ge E - S - T_{\text{tax}} + (\Delta W \times C_w)$$

- **The Denver Nuggets Benchmark (June 27, 2024):**
  At the June 27, 2024 decision time, pre-free agency salary projections positioned Denver at ~$\$193.0\text{M}$ (~$\$4.1\text{M}$ over the 2024–25 Second Apron of $\$188.93\text{M}$, assuming Kentavious Caldwell-Pope re-signed). Denver traded Reggie Jackson ($\$5.25\text{M}$) and **three future 2nd-round draft picks** to Charlotte for zero return. (Subsequently, KCP departed in free agency, leaving realized end-of-season payroll at $\$182.57\text{M}$, or $\$187.82\text{M}$ with Jackson, $\$1.1\text{M}$ below the apron).
  - In public draft equity literature (Pelton, Cranston, 538), mid-to-high 2nd round picks hold an average surplus equity of $\approx \$2.67\text{M}$ each ($3 \times \$2.67\text{M} \approx \$8.0\text{M}$).
  - **Costs and Savings:** Denver gave up 3 second-round picks ($E \approx \$8.0\text{M}$) and saved $S = \$5.25\text{M}$ in salary, a pre-tax net cost of $\$2.75\text{M}$. But Denver was deep in the luxury tax, so the dump also saved $T_{\text{tax}} \approx \$14.3\text{M}$ (2023 CBA incremental schedule, non-repeater rates, realized 2024–25 payroll; $\approx \$17.8\text{M}$ on the decision-time payroll). **Net cost after tax: $\approx -\$11.5\text{M}$.** Denver came out ahead in cash before counting any friction relief.
  - **Revealed-Preference Bound:**
    $$\lambda_3 \ge \frac{E - S - T_{\text{tax}} + \Delta W \cdot C_w + 0.35 \times B_{\text{post}}}{B_{\text{pre}}} \ge \mathbf{0.08} \quad (\text{or } \mathbf{0.14} \text{ if Jackson cost } 0.5\text{ WAR})$$
    with $B_{\text{pre}} = \$42.25\text{M}$, $B_{\text{post}} = \$42.05\text{M}$.
  - **Conclusion: non-binding.** Both bounds sit below $\lambda_2 = 0.35$, which the model already requires. Tax cash alone justifies the dump, so salary dumps by deep-tax teams **cannot identify $\lambda_3$**. An earlier version omitted $T_{\text{tax}}$, reported $\lambda_3 \ge 0.41$, and compared it to a 0.46 break-even taken from a setup where $\lambda_2$ also shrinks. The bound was wrong and the comparison mismatched (see the audit trail). Second Apron drag has to be judged against the statutory cost breakdown in `config.py` instead.

### 2. Econometric Discontinuity, Placebo Controls & Multi-Season Bunching (2020–2026)
In public finance (Kleven 2016), **bunching estimation** identifies behavioral notch-effects. Analyzing all 180 team-seasons across 2020–2026 reveals:
- **Second Apron Bunching & Statistical Power:** Post-2023 CBA payrolls show suggestive bunching within the tight **$-\$5\text{M}$ to $\$0$ band** immediately below the Second Apron (6 post-CBA team-seasons: NYK $-\$0.37\text{M}$, GSW $-\$3.70\text{M}$, LAL $-\$0.91\text{M}$, MIL $-\$0.57\text{M}$).
  - *Placebo Line:* Because the Second Apron did not exist pre-2023, pre-2023 comparison data is an explicit **synthetic placebo line**.
  - *Fisher Exact Test:* A two-sided Fisher Exact Test on Second Apron bunching yields $p \approx 0.50$ (ratio within $\pm\$5\text{M}$ yields $p = 1.00$). We candidly acknowledge that with $N=90$ team-seasons, Second Apron bunching is statistically underpowered.
- **Verified Luxury Tax Bunching:** In contrast, the Luxury Tax threshold has existed across both eras. Within $\pm\$3\text{M}$ of the tax line, teams bunch heavily below rather than above:
  - *Pre-CBA (2020–2023):* **24 below vs. 1 above**
  - *Post-CBA (2023–2026):* **23 below vs. 6 above**
  - This confirms that NBA front offices demonstrably respond to statutory financial cliffs when penalties bite.
- **Contender Attrition:** Franchises willing to stay above the Second Apron collapsed from **4 teams (2023–24)** $\to$ **3 teams (2024–25)** $\to$ **only 1 team (CLE in 2025–26)**, a **$-75\%$ attrition rate**.

---

## Sensitivity Grid, Uncertainty Analysis & Escape Menu

The engine includes a dedicated sensitivity and optimization suite ([`boardman/sensitivity.py`](boardman/sensitivity.py)):

### 1. Grounding λ₃ in Sourced Cost Components & Flagship Pair Simulation (`calculate_headline_uncertainty`, `calculate_flagship_uncertainty_pair`)
Rather than drawing $\lambda_3$ from an arbitrary $\text{Uniform}(0.40, 0.85)$ distribution, `boardman` grounds $\lambda_3$ directly in the **four explicit statutory cost components of the 2023 CBA** ([`boardman/config.py`](boardman/config.py)):

| Cost Component | Statutory Basis | Citation & Empirical Basis | Low ($) | High ($) | Midpoint ($) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Frozen 1st Pick & Pick 30 Demotion** | Art. VII Sec. 7(g) | 538 / Kevin Pelton (ESPN) / Cranston draft surplus curves | $\$6.0\text{M}$ | $\$8.5\text{M}$ | $\$7.3\text{M}$ |
| **Loss of Taxpayer MLE (TP-MLE)** | Art. VII Sec. 6(b)(iii) | Spotrac / HoopsHype contract market value for rotation MLEs | $\$4.8\text{M}$ | $\$6.2\text{M}$ | $\$5.4\text{M}$ |
| **Aggregation & Cash Illiquidity** | Art. VII Sec. 8(e) | Amihud & Mendelson 1986 / Silber 1991 illiquidity discount (10%–15%) | $\$6.5\text{M}$ | $\$10.5\text{M}$ | $\$8.0\text{M}$ |
| **Repeater Tax Surcharge & Buyout Ban** | Art. VII Sec. 8(c) & Sec. 12 | Larry Coon CBA FAQ & historical repeater tax acceleration schedules | $\$6.0\text{M}$ | $\$11.0\text{M}$ | $\$8.5\text{M}$ |

Total annual economic drag across the four components spans **$\$23.3\text{M}$ to $\$36.2\text{M}$** (midpoint **$\approx \$29.2\text{M}$**). Across Cleveland's roster quadratic base ($B_{\text{pre}} = \$44.39\text{M}$), this implies $\lambda_3 \in [0.525, 0.816]$ with a mean of **$0.66$**.

In our 10,000-trial Monte Carlo simulation, $\lambda_3$ is drawn by summing random draws from each of these four sourced distributions and dividing by $B_{\text{pre}}$, paired with player measurement noise ($\sigma_{\text{WAR}} = 0.35$).

**Results for the Flagship Pair:**
- **💎 Flagship 1 (Robust Flip: Max Strus → Caleb Martin, DAL):**
  - Break-Even: $\lambda_3 \ge 0.356$ (Required friction relief: only $\$613\text{K}$).
  - **Win Probability:** **$100.0\%$** of draws.
  - **Mean Scenario $\Delta NSV$:** **$+\$13.90\text{M}$** (90% scenario interval: $[+\$9.44\text{M}, +\$18.34\text{M}]$).
- **⚡ Flagship 2 (High-Stakes Gamble: Jarrett Allen → Isaiah Stewart, DET):**
  - Break-Even: $\lambda_3 \ge 0.779$ (Required friction relief: $\$19.42\text{M}$).
  - **Win Probability:** **$3.5\%$** of draws.
  - **Mean Scenario $\Delta NSV$:** **$-\$4.81\text{M}$** (90% scenario interval: $[-\$9.24\text{M}, -\$0.31\text{M}]$).

### 2. True 2D Sensitivity Grid (`analyze_trade_sensitivity`)
- Evaluates parameter elasticity across scaled $\lambda$ ($0.0\times$ to $2.0\times$) and Cost-Per-Win ($C_w$).
- At $\lambda = 0.00$, $\Delta NSV$ **strictly equals the linear $/WAR result ($-\$10.53\text{M}$)**.
- As $\lambda$ scales, $\Delta NSV$ rises monotonically, turning positive at about $0.66\times$ baseline. Because the grid scales every bracket together, that point is $\lambda_3 \approx 0.46$ **with $\lambda_2 \approx 0.23$**. It is not comparable to the fixed-$\lambda_2$ break-even of 0.58.

### 3. The Apron Escape Frontier: Allowable Talent Sacrifice Curve (`calculate_apron_escape_frontier`)
- **Linear Model:** Shedding $\$5.0\text{M}$ justifies sacrificing at most **$-0.96$ WAR**.
- **Board Man Apron Model (baseline $\lambda_3 = 0.70$):** Dropping below the Second Apron unlocks **$+\$15.93\text{M}$ in friction relief**, expanding the allowable talent sacrifice to **$-3.93$ WAR (a 4.1x expansion)**.

### 4. Cleveland Second Apron Escape Menu (`scan_apron_escape_trades`)
The scan ranks Cleveland's legal 1-for-1 swaps that get under the Second Apron and flip a linear reject into an accept. It uses the **multi-season WAR prior** and **protects Cleveland's top three players** (Mitchell, Harden, Mobley) by default: an earlier single-season version recommended trading Evan Mobley for Brandon Ingram, which no front office would do.

| Cleveland Outgoing | Partner Franchise | Incoming Player | Salary Shed | On-Court WAR Loss | Linear $/WAR Verdict | Board Man Net Surplus |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **Max Strus** | CHI | Jaden Ivey | $\$5.8\text{M}$ | $-1.14$ WAR | $-\$0.1\text{M}$ | **$+\$15.7\text{M}$** |
| **Sam Merrill** | UTA | Kevin Love | $\$4.3\text{M}$ | $-1.14$ WAR | $-\$1.6\text{M}$ | **$+\$14.0\text{M}$** |
| **Jarrett Allen** | POR | Robert Williams | $\$6.7\text{M}$ | $-1.78$ WAR | $-\$2.6\text{M}$ | **$+\$13.4\text{M}$** |
| **Dennis Schröder** | WAS | Tre Johnson | $\$5.9\text{M}$ | $-2.78$ WAR | $-\$8.7\text{M}$ | **$+\$7.2\text{M}$** |

*Multi-season WAR prior (`war_projected`), baseline $\lambda_3 = 0.70$. Mitchell, Harden and Mobley are protected (`protect_top_n=3`). 30 flips across 15 partner teams.*

### 5. League Ranking Elasticity (`calculate_ranking_elasticity`)
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
│   ├── sensitivity.py       # Break-even λ₃, scenario simulation, sensitivity grid, frontier, escape scan & ranking elasticity
│   ├── trade_engine.py      # Multi-team swap simulator & delta surplus
│   ├── valuation.py         # Fair Value, GSV, Friction Tax, and NSV formulas
│   └── data/
│       └── ingest.py        # Ingestion pipeline joining salaries, stats & prior history
├── data/
│   └── processed/
│       ├── master_players_2025_26.parquet  # 659 contracts + metrics + multi-season projected WAR
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
├── tests/                   # Automated unit tests (39/39 passing in ~2s)
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
1. **📊 League Surplus Board:** Interactive Plotly scatter plot mapping **Cap Hit** vs. **Fair Production Value**, color-coded by Apron Bracket, with toggleable Multi-Season Blended WAR Prior.
2. **🔄 CBA Trade Machine:** Multi-team swap simulator with live statutory compliance checking, dead-money filtering, presets (including the robust Strus ↔ Martin flip and Allen ↔ Stewart gamble), and $\Delta NSV$ cards.
3. **📈 Sensitivity & Frontier:** Live break-even $\lambda_3$, scenario simulation over 4 sourced statutory cost components, 2D sensitivity heatmap, talent sacrifice frontier, Cleveland apron escape menu, and ranking elasticity.
4. **📉 Empirical Evidence: Discontinuity & Dumps:** Econometric bunching distribution chart (2020–2026) and the tax-inclusive Denver/Reggie Jackson derivation showing that salary dumps do not bound $\lambda_3$.
5. **💼 'Uncle Dennis' Lab:** Kawhi Leonard circumvention simulator with shadow compensation slider, risk-adjusted expected penalty math, and investigative citations.
6. **🔬 Audit Trail & Limitations:** Direct answers to datathon questions, dead-money provenance audit, multi-season blended talent prior, and AI auditing log.

---

## Benchmark Case Studies

1. **The Cleveland Apron Escape Flagship Pair:** Contrast between a robust, no-brainer flip (Max Strus to DAL for Caleb Martin: sheds $6.34M, 100% win probability across sourced cost components) and an assumption-dependent gamble on extreme friction severity (Jarrett Allen to DET for Isaiah Stewart: sheds $5M, sacrifices 4.67 WAR, requires $\lambda_3 \ge 0.78$).
2. **The Kawhi Leonard Circumvention Ruling (Sept 2026):** Models the risk-adjusted expected penalty:
   $$\mathbb{E}[\text{Penalty}] = P(\text{audit}) \times [\text{Fine } (\$30\text{M}) + 5\text{ Picks } (\$57.5\text{M})] = \$26.25\text{M}$$
   *(Exploratory parameter assumptions based on reporting from Pablo Torre and Wachtell Lipton's retention by the NBA Board of Governors).*
3. **The Cleveland Second Apron Aggregation Trap:** Demonstrates automatic rejection under the 2023 CBA zero salary aggregation rule.
4. **The Spurs-Celtics Liquidity Swap:** Shows how San Antonio captures +$36.8M in Net Surplus by leveraging sub-tax cap room.

*(Full walkthroughs in [`docs/case_studies.md`](docs/case_studies.md).)*

---

## What We Checked & Model Limitations

### Econometric Discontinuity, Placebos & Historical Dumps
- **Discontinuity Bunching & Placebo Line (2020–2026):** Post-2023 NBA payrolls exhibit suggestive bunching immediately below the Second Apron ($-\$5\text{M}$ to $\$0$ band: NYK $-\$0.37\text{M}$, GSW $-\$3.70\text{M}$, LAL $-\$0.91\text{M}$, MIL $-\$0.57\text{M}$), while over-apron contenders collapsed by $-75\%$. A two-sided Fisher Exact Test yields $p \approx 0.50$ against the pre-2023 synthetic placebo line (statistically underpowered at $N=90$). In contrast, Luxury Tax bunching (24 below vs 1 above pre-CBA; 23 below vs 6 above post-CBA) demonstrates verified behavioral responsiveness to statutory thresholds.
- **Salary Dumps Do Not Identify λ₃:** Denver gave up $3$ second-round picks ($\approx \$8.0\text{M}$) to shed Reggie Jackson's $\$5.25\text{M}$, but as a deep-tax team also saved $\approx \$14.3\text{M}$ in luxury tax. Tax cash alone justifies the dump; the implied bound ($\lambda_3 \ge 0.08$, or $0.14$ with a 0.5 WAR loss) is below $\lambda_2 = 0.35$ and non-binding.
- **λ Is a Scenario Input:** The headline is therefore stated conditionally: the CLE–DET trade flips if escaping the Second Apron is worth ≥ \$10.53M/yr ($\lambda_3 \ge 0.58$). Whether that holds rests on the statutory cost breakdown in `config.py` (frozen pick, lost taxpayer MLE, aggregation illiquidity, repeater surcharges), which we argue totals roughly \$25M–\$32M/yr for Cleveland.

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

### Multi-Season Blended WAR Prior (`war_projected`)
Single-season box scores naturally penalize injured stars (e.g. Tyrese Haliburton, Jayson Tatum during missed games). `boardman` resolves this by establishing the **Multi-Season Blended WAR Prior (`war_projected`)** as the primary default impact metric throughout the entire engine. This regresses single-season box scores against 3-year historical baselines (Marcel-style weighted regression approach). Under this model, Tatum and Haliburton are recognized as positive star assets, and underwater contracts like Zach LaVine, Khris Middleton, and Jordan Poole correctly occupy the bottom ranks.

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
4. **Salary Dump Directional Sign Error:**
   - *The Issue:* An initial draft of revealed preference lambda added salary shed to pick equity rather than subtracting it, failing to recognize that shedding salary saves cash in the team's favor.
   - *The Fix:* Corrected net cost paid to $E - S = \$8.0\text{M} - \$5.25\text{M} = \$2.75\text{M}$, dropping artificial upper bounds. (This bound still omitted luxury tax; see item 6.)
5. **Synthetic Placebo Line & Fisher Exact Reporting:**
   - *The Issue:* Comparing post-2023 payroll bunching to pre-2023 data without acknowledging that the Second Apron did not exist pre-2023.
   - *The Fix:* Formally labeled the pre-2023 line as a synthetic placebo line, computed two-sided Fisher Exact tests ($p \approx 0.50$), and emphasized that while Second Apron data is underpowered ($N=90$), luxury tax line bunching demonstrates verified behavioral response.
6. **Omitted Luxury Tax Term in the Denver Bound:**
   - *The Issue:* The revealed-preference inequality included $T_{\text{tax}}$, but the computation dropped it and reported $\lambda_3 \ge 0.41$. Denver saved ~\$14M in tax, far more than the \$2.75M net pick cost.
   - *The Fix:* Implemented the 2023 CBA incremental tax schedule (`calculate_luxury_tax`). The corrected bound ($\lambda_3 \ge 0.08$) is non-binding, and we now state that salary dumps do not identify $\lambda_3$.
7. **Mismatched Break-Even Comparison:**
   - *The Issue:* A hardcoded break-even of $\lambda_3 = 0.46$ came from the sensitivity grid, which scales $\lambda_2$ down along with $\lambda_3$. It was compared against a bound and a Monte Carlo that hold $\lambda_2 = 0.35$ fixed, where the true break-even is 0.58.
   - *The Fix:* `calculate_break_even_lambda_3` solves the break-even live from the trade engine; a test checks it matches the Monte Carlo's closed form. The Monte Carlo interval is relabeled a scenario interval, since the $\lambda_3$ range is assumed.
8. **Escape Menu Recommending Cornerstone Trades:**
   - *The Issue:* Ranked on single-season WAR, the escape menu's top suggestions included trading Evan Mobley for Brandon Ingram.
   - *The Fix:* The scan now defaults to the multi-season WAR prior and protects the team's top three players (`protect_top_n=3`).

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
tests/test_empirical_dumps.py::test_calculate_luxury_tax PASSED
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
tests/test_sensitivity.py::test_calculate_headline_uncertainty PASSED
tests/test_sensitivity.py::test_calculate_break_even_lambda_3 PASSED
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

============================== 36 passed in 2.16s ==============================
```


