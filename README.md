# Board Man Gets Paid (`boardman-gets-paid`)

> Modern NBA Collective Bargaining Agreement (CBA) Roster Constraint & Apron Friction Valuation Engine.

**Author:** Jace Kasen  
**Status:** In Active Development

---

## Overview

Traditional sports analytics valuation models (such as Dollar-per-WAR or Dollar-per-VORP) evaluate player value linearly: *If Player X produces $20M of on-court value and earns $10M, they yield +$10M in surplus.*

However, under the modern **2023 NBA Collective Bargaining Agreement (CBA)**, roster flexibility is deeply non-linear. Exceeding the **Luxury Tax First and Second Aprons** imposes severe operational penalties:
- **First Apron:** 100% hard salary matching; loss of the bi-annual exception.
- **Second Apron:** Elimination of salary aggregation in trades, forfeiture of the taxpayer mid-level exception (MLE), zero outgoing cash allowed, and frozen/demoted first-round draft picks 7 years out.

`boardman-gets-paid` introduces the **Apron Friction Tax ($\lambda$)** to quantify the operational and opportunity-cost drag of contracts on high-payroll franchises, pricing true **Net Surplus Value ($NSV$)** and evaluating trades under statutory CBA legality.

---

## Mathematical Architecture

### 1. Fair Production Value ($FV$)
Calculated from standardized public impact metrics (VORP and Win Shares):

$$\hat{W}_i = 2.70 \times \text{VORP}_i$$

$$FV_i = \hat{W}_i \times \text{Cost Per Win}$$

$$\text{Gross Surplus Value } (GSV_i) = FV_i - \text{Cap Hit}_i$$

### 2. Apron Friction Tax ($\lambda$)
Penalizes roster-inflexible contracts on high-payroll teams:

$$\text{Friction}_i = \lambda(T) \times \text{Cap Hit}_i \times \left(\frac{\text{Cap Hit}_i}{\text{Salary Cap}}\right)$$

$$NSV_i = GSV_i - \text{Friction}_i$$

Where $\lambda(T)$ is conditioned on the franchise's payroll bracket $T$:
- **Bracket 0 ($< \text{Luxury Tax}$):** $\lambda = 0.00$ (full roster flexibility)
- **Bracket 1 ($\text{Tax} \to \text{First Apron}$):** $\lambda = 0.15$
- **Bracket 2 ($\text{First} \to \text{Second Apron}$):** $\lambda = 0.35$
- **Bracket 3 ($> \text{Second Apron}$):** $\lambda = 0.70$ (frozen draft capital, asset illiquidity)

### 3. Trade Net Surplus Delta ($\Delta NSV$)
Captures the shift in total roster surplus and apron bracket relief post-trade:

$$\Delta NSV_{\text{Team}} = \sum_{k \in \text{Roster}_{\text{post}}} NSV_k(T_{\text{post}}) - \sum_{k \in \text{Roster}_{\text{pre}}} NSV_k(T_{\text{pre}})$$

---

## Project Structure

```text
boardman-gets-paid/
├── boardman/
│   ├── __init__.py
│   ├── config.py           # CBA financial thresholds, tax brackets, constants
│   ├── schema.py           # Pydantic data schemas
│   ├── data/
│   │   ├── __init__.py
│   │   └── ingest.py       # Ingestion & join pipeline from ~/dev/nba
│   ├── valuation.py        # FV, GSV, Friction Tax, and NSV formulas
│   ├── cba_rules.py        # Statutory trade matching & apron restrictions
│   └── trade_engine.py     # Multi-team swap simulator & delta surplus
├── data/
│   ├── raw/                # Extracted source tables
│   └── processed/          # Master joined tables (contracts + VORP/WS + brackets)
├── tests/
│   ├── __init__.py
│   └── test_*.py           # Unit tests for valuation and trade rules
├── app/                    # Streamlit visual evaluator
├── pyproject.toml
└── requirements.txt
```

---

## Installation & Setup

1. Activate your NBA conda environment:
   ```bash
   conda activate nba
   ```

2. Install `boardman-gets-paid` in editable development mode:
   ```bash
   cd ~/dev/boardman-gets-paid
   pip install -e ".[dev]"
   ```

3. Run the automated test suite:
   ```bash
   pytest
   ```
