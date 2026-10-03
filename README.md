# Board Man Gets Paid (`boardman-gets-paid`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.3-black.svg)](frontend/)

> **NBA Contract Efficiency & Surplus Value Arbitrage Board.**  
> Pinpointing the most efficient production-value-to-salary contracts in the NBA for fans, analysts, and front offices.

**Author:** Jace Kasen · **License:** MIT · Python 3.10+ & Next.js 16 (React 19)

---

## 1. The Core Problem: Surplus Value Arbitrage

In the modern NBA, team payrolls are tightly constrained by the Collective Bargaining Agreement (CBA) salary cap ($154.6M), luxury tax ($187.9M), and first/second apron thresholds ($195.9M / $207.8M). Because rosters are hard-capped in flexibility once payroll escalates, **contract efficiency is the supreme operational edge**:

- **Statutory Bargains:** Players whose on-court production vastly outpaces their statutory cap hit—such as superstar rookie-scale deals (e.g. Victor Wembanyama producing +$58M in net surplus on a capped $13.4M salary) or elite underpaid rotation players.
- **Franchise Anchors:** High-salary players whose production has degraded below their cap hit (e.g. underwater max contracts generating -$30M to -$36M in negative surplus), dragging their teams into punitive tax brackets without corresponding wins.
- **Supermax Outperformers:** Elite MVP-caliber stars (e.g. Nikola Jokić, Shai Gilgeous-Alexander) who produce so many wins above replacement that they still generate enormous positive surplus ($70M+) despite earning the 35% supermax.

`boardman-gets-paid` is an interactive microproduct that maps player on-court win production against contract cap allocations, providing an intuitive, transparent explorer for contract efficiency and surplus arbitrage across the 2025–26 NBA season.

---

## 2. Key Insights & Headline Anomalies

| Category | Player | Team | Tier | Salary | Proj. WAR | Production Value | Net Surplus | ROI Multiple |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **#1 League Surplus Leader** | **Nikola Jokić** | DEN | Max / Supermax | $55.2M | 25.70 | $133.5M | **+$78.2M** | **2.42x** |
| **#2 League Surplus Leader** | **Shai Gilgeous-Alexander** | OKC | Max / Supermax | $38.3M | 21.40 | $111.1M | **+$72.8M** | **2.90x** |
| **Top Rookie-Scale Bargain** | **Victor Wembanyama** | SAS | Rookie Scale | $13.4M | 13.80 | $71.7M | **+$58.3M** | **5.36x** |
| **Top High-ROI Starter** | **Chet Holmgren** | OKC | Rookie Scale | $13.7M | 10.90 | $56.6M | **+$42.9M** | **4.12x** |
| **Top Anchor Contract** | **Zach LaVine** | SAC | Max / Supermax | $47.5M | 2.00 | $10.4M | **-$37.1M** | **0.22x** |
| **Top Anchor Contract** | **Paul George** | PHI | Max / Supermax | $51.7M | 3.50 | $18.2M | **-$36.6M** | **0.35x** |
| **Top Anchor Contract** | **Khris Middleton** | DAL | Mid-Level | $33.3M | -0.50 | -$2.6M | **-$35.9M** | **0.00x** |

---

## 3. Mathematical Valuation Architecture

### A. Production Metric ($\hat{W}$)
To maintain an open, reproducible framework without paywalled proprietary metrics, the engine employs a multi-season Marcel-style talent prior (`war_projected`):
- Combines current-season box-score impact with historical player priors (60% weight on 2024–25, 40% on 2023–24).
- Wins Above Replacement (WAR) is calibrated from Value Over Replacement Player (VORP) as:
  $$\hat{W}_{\text{VORP}} = 2.70 \times \text{VORP}$$
- Regresses realized production against the prior (65% current, 35% prior) to stabilize single-season injury volatility.
- Players with zero minutes receive an injury discount against their historical baseline.

### B. Unconstrained Veteran Cost Per Win ($C_w$)
To prevent rookie-scale bargains from artificially depressing the market cost of a win, $C_w$ is calibrated exclusively on **unconstrained veteran contracts** (veterans earning $\ge \$5.0\text{M}$ with positive WAR):

$$C_w = \frac{\sum_{j \in \text{Veterans}} \text{Cap Hit}_j}{\sum_{j \in \text{Veterans}} \hat{W}_j} = \$5,193,442.76 \text{ per Win}$$

### C. Fair Production Value ($FV$) & Net Surplus ($NSV$)
$$\text{Fair Value } (FV_i) = \hat{W}_i \times C_w$$
$$\text{Net Surplus } (NSV_i) = FV_i - \text{Cap Hit}_i - \text{Friction Tax}_i$$

Where the **Apron Friction Tax** applies quadratic drag on high-payroll teams above luxury tax aprons:
$$\text{Friction}_i = \lambda(T) \times \text{Cap Hit}_i \times \left(\frac{\text{Cap Hit}_i}{\text{Salary Cap}}\right)$$

### D. ROI Efficiency Multiple
For all verified cap hits, the **ROI Multiple** measures dollar-for-dollar return:
$$\text{ROI Multiple} = \frac{\text{Fair Production Value}}{\text{Cap Hit}}$$
*(e.g., 5.36x for Victor Wembanyama; 0.22x for Zach LaVine; N/A for unverified two-way deals)*.

---

## 4. Rigorous Data Integrity & Quality

Following rigorous evaluation, the data pipeline includes full statutory contract accounting:

1. **Self-Contained In-Repo Data:** All raw salary books, season histories, and box scores are packaged inside `data/raw/` (under 30 MB). Full ingestion and valuations reproduce from a clean repository clone with zero external machine dependencies.
2. **Active vs. Dead Money Deduplication (Zero Active Duplicates):** Multi-team stint tracking identifies each player's latest regular-season team. Stretched and waived prior obligations (e.g. Kyle Anderson on Memphis, Damian Lillard on Portland) are marked as dead money obligations with strictly **0.00 WAR**, ensuring that every player in the league has **strictly at most one active roster contract**.
3. **Explicit Salary Quality & Tiers:** 146 two-way and unverified mid-season additions with missing salaries are explicitly flagged (`is_salary_known = False`, `tier: "Two-Way / Unknown"`). They are never treated as $0-cost free surplus superstars, and cannot divide by zero.
4. **Contract Tier Taxonomy:** Contracts are classified into 5 canonical tiers:
   - **Rookie Scale:** Capped entry contracts (years in league $\le 4$, salary $\le \$16\text{M}$).
   - **Max / Supermax:** Franchise cornerstones ($\ge \$35\text{M}$ cap hit).
   - **Mid-Level:** Rotation contracts ($\$8\text{M} - \$35\text{M}$).
   - **Minimum / Rotation:** Value deals ($< \$8\text{M}$).
   - **Two-Way / Unknown:** Non-guaranteed or unverified cap allocations.

---

## 5. Project Layout

```text
boardman-gets-paid/
├── boardman/                 # Python valuation & ingestion package
│   ├── config.py             # Statutory 2025-26 CBA thresholds & paths
│   ├── data/
│   │   └── ingest.py         # Stint deduplication & master parquet builder
│   ├── schema.py             # Pydantic schemas (PlayerRecord, TeamRecord)
│   ├── valuation.py          # Fair Value, Net Surplus, ROI, & Leaderboards
│   └── web_api.py            # Static JSON snapshot bridge
├── data/
│   ├── raw/                  # Packaged raw data (salaries, stats, EPM)
│   └── processed/            # Master parquets & QA ingestion report
├── frontend/                 # Interactive Next.js 16 Web Dashboard
│   ├── src/
│   │   ├── components/       # Dashboard, table filters, scatter plot, modal
│   │   └── data/league.json  # Precomputed snapshot data
├── tests/                    # Pytest regression suite (16 tests)
│   ├── test_ingest.py        # Data integrity, deduplication, & tiers
│   ├── test_valuation.py     # Valuation math, dead money, & ROI
│   └── test_web_api.py       # JSON schema & snapshot compliance
└── docs/                     # Methodology documentation
```

---

## 6. Quickstart & Reproduction

### Python Environment
Requires Python 3.10+:

```bash
# Clone the repository
git clone https://github.com/jankasen/boardman-gets-paid.git
cd boardman-gets-paid

# Run automated test suite (16 tests pass in < 1 second)
pytest -v

# Re-run data ingestion from packaged raw sources
python -m boardman.data.ingest
```

### Next.js Dashboard
Requires Node.js 18+:

```bash
cd frontend
npm install

# Run development server
npm run dev

# Or build static production bundle
npm run build
```

Open `http://localhost:3000` to interact with the Surplus Board.

---

## 7. Interactive Explorer Features

- **Quick Presets:** Instant filter toggles for **Top Bargains** (positive surplus), **Top Anchors** (underwater contracts), and **Highest ROI Multiple**.
- **Tier & Team Filtering:** Drill down by contract tier (Rookie Scale, Max/Supermax, Mid-Level, Minimum) or any of the 30 NBA franchises.
- **Contract Detail Modal:** Inspect any player's Fair Production Value, Cap Hit, Apron Friction, Gross Surplus, and ROI Multiple.
- **CSV Export:** One-click download of the filtered surplus board for custom modeling and editorial research.

---

## 8. License

MIT License. Created by Jace Kasen. Data sourced from public Basketball-Reference and NBA salary archives.
