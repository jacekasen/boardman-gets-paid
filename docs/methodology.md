# Valuation Methodology & Economic Architecture

`boardman-gets-paid` prices NBA player contracts against modern Collective Bargaining Agreement (CBA) constraints. Standard sports analytics valuation models evaluate contract value linearly, ignoring the steep operational penalties imposed by the Luxury Tax First and Second Aprons.

---

## 1. The Fallacy of Linear Valuation

Traditional sports surplus models (such as Dollar-per-WAR or Dollar-per-VORP) evaluate contract value with a simple linear equation:

$$\text{Surplus Value} = (\hat{W} \times C_w) - \text{Cap Hit}$$

Where $\hat{W}$ is player win contribution and $C_w$ is the league-wide cost of a win.

### Why This Fails in the Modern NBA
Under the **2023 NBA CBA**, a dollar spent by a sub-tax franchise (e.g., Utah, San Antonio) does **not** have the same economic utility as a dollar spent by a franchise above the Second Apron (e.g., Cleveland, Phoenix, Boston):

1. **Quadratic Tax Penalties:** Luxury tax rates escalate exponentially into repeater tiers ($3.75 to $4.75+ per dollar over the threshold).
2. **Operational Bans:** Crossing the Second Apron freezes first-round draft picks 7 years out, moves picks to the end of the round if repeated, revokes the mid-level exception, and eliminates salary aggregation in trades.
3. **Asset Illiquidity:** A $40M player on a Second Apron team cannot be traded for two $20M players; the team cannot take back more money than sent out, nor can they send cash.

`boardman-gets-paid` introduces the **Apron Friction Tax ($\lambda$)** to quantify this non-linear drag.

---

## 2. Public One-Number Metric Standardization

To maintain an open-source framework without relying on paywalled or proprietary metrics (such as EPM), the engine standardizes publicly accessible box-score metrics from Basketball-Reference:

### A. Value Over Replacement Player (VORP)
VORP measures a player's box-score impact relative to a replacement-level player (defined as $-2.0$ BPM), weighted by minutes played and normalized to an 82-game schedule:

$$\text{VORP} = \left[\text{BPM} - (-2.0)\right] \times \left(\frac{\% \text{ of team minutes}}{100}\right) \times \left(\frac{\text{team games}}{82}\right)$$

### B. Wins Above Replacement Conversion ($\hat{W}_{\text{VORP}}$)
Based on historical regression across NBA box scores, Basketball-Reference calibrates:

$$\hat{W}_{\text{VORP}} = 2.70 \times \text{VORP}$$

### C. Blended Win Contribution ($\hat{W}_{\text{Blend}}$)
The engine also supports an ensemble weighting between VORP-based WAR and Win Shares (WS):

$$\hat{W}_{\text{Blend}} = 0.5 \times (2.70 \times \text{VORP}) + 0.5 \times \text{WS}$$

---

## 3. Calibration of Open-Market Cost Per Win ($C_w$)

If all active contracts (including rookie-scale deals and minimum contracts) are pooled together, rookie deals like Victor Wembanyama producing superstar value on $13M heavily depress the calculated cost per win.

To prevent this distortion, `boardman-gets-paid` calibrates $C_w$ using **unconstrained veteran contracts** (contracts $\ge \$5.0\text{M}$ with positive WAR):

$$C_w = \frac{\sum_{j \in \text{Veterans}} \text{Cap Hit}_j}{\sum_{j \in \text{Veterans}} \max(0, \hat{W}_j)}$$

### 2025–26 Empirical Baseline
- **League Salary Cap:** $\$154,647,000$
- **Total Qualified Veteran Payroll:** $\$5,563,301,163$ across 513 players.
- **Calibrated Cost Per Win ($C_w$):** **$\$5,229,871.98$** per win above replacement.

---

## 4. Fair Production Value ($FV$) & Gross Surplus ($GSV$)

Using the calibrated cost per win:

$$\text{Fair Production Value } (FV_i) = \hat{W}_i \times C_w$$

$$\text{Gross Surplus Value } (GSV_i) = FV_i - \text{Cap Hit}_i$$

- **Positive $GSV$:** Represents an on-court bargain or discount relative to open-market production.
- **Negative $GSV$:** Represents an overpayment or on-court deficiency relative to salary.

---

## 5. Hypothesized Opportunity-Cost Breakdown for the Apron Friction Tax ($\lambda$)

To model the operational and opportunity-cost drag of contracts on high-payroll franchises:

$$\text{Friction}_i = \lambda(T) \times \text{Cap Hit}_i \times \left(\frac{\text{Cap Hit}_i}{\text{Salary Cap}}\right)$$

Where $\lambda(T)$ is a discrete operational multiplier conditioned on the franchise's payroll bracket $T$:

| Bracket $T$ | Payroll Range | Operational Multiplier $\lambda(T)$ | Franchise Restrictions | Hypothesized Opportunity-Cost Basis |
| :---: | :---: | :---: | :--- | :--- |
| **0** | $< \text{Luxury Tax}$ ($\$187.9\text{M}$) | **$0.00$** | Full roster flexibility, escalated matching bands. | Zero regulatory restriction. |
| **1** | $\text{Tax} \to \text{1st Apron}$ ($\$195.9\text{M}$) | **$0.15$** | Cash luxury tax penalties; Bi-Annual preserved. | Marginal cash tax ($1.50x to $2.50x) + initial liquidity discount. |
| **2** | $\text{1st} \to \text{2nd Apron}$ ($\$207.8\text{M}$) | **$0.35$** | Hard 100% salary matching; loss of Bi-Annual. | Forfeiture of BAE (~$4.7M) + 100% hard matching constraint. |
| **3** | $> \text{Second Apron}$ ($\$207.8\text{M}$) | **$0.70$** | Frozen 7-yr picks; zero aggregation; zero cash. | Estimated from assumed CBA penalties: Pick freeze/demotion (~$7.3M) + lost TP-MLE (~$5.4M) + illiquidity discount (~$8.0M) + tax surcharges (~$10.0M) = **~$31.0M annual drag**. |

### Detailed Breakdown of Bracket 3 ($\lambda = 0.70$)
1. **Frozen Draft Pick & End-of-Round Demotion ($\approx \$7.3\text{M}$):**
   - Under CBA rules, a Second Apron team's 7-year out 1st-round pick is frozen. If they repeat, it drops to pick 30.
   - Historical rookie contract surplus curves demonstrate that an average middle-first pick (#15–#20) generates $\approx \$10.5\text{M}$ in net surplus over 4 years, whereas pick #30 generates only $\approx \$3.2\text{M}$. Expected loss = **$\$7.3\text{M}$**.
2. **Forfeiture of the Taxpayer Mid-Level Exception ($\approx \$5.4\text{M}$):**
   - Second Apron teams cannot use the TP-MLE ($5.4M market value), forcing them to fill rotation depth exclusively with minimum contracts.
3. **Asset Illiquidity & Aggregation Ban ($\approx \$7.5\text{M}$–$\$10.0\text{M}$):**
   - The inability to aggregate multiple contracts or send cash creates a 10%–15% illiquidity haircut on high-salary player trades.
4. **Sum of Penalties:** Combining these assumed opportunity costs yields **$\approx \$25\text{M}$–$\$32\text{M}$** in annual structural drag, which $\lambda = 0.70$ approximates on Cleveland's calculated roster friction of **$\$31.07\text{M}$**.

### Quadratic Drag Property
Notice the quadratic term:

$$\text{Cap Hit}_i \times \frac{\text{Cap Hit}_i}{\text{Salary Cap}} = \frac{(\text{Cap Hit}_i)^2}{\text{Salary Cap}}$$

- A **$\$20\text{M}$ starter** in Bracket 3 pays:
  $$\text{Friction} = 0.70 \times 20\text{M} \times \frac{20\text{M}}{154.6\text{M}} \approx \$1.81\text{M}$$
- A **$\$40\text{M}$ supermax** in Bracket 3 pays:
  $$\text{Friction} = 0.70 \times 40\text{M} \times \frac{40\text{M}}{154.6\text{M}} \approx \$7.24\text{M}$$

Doubling the contract size **quadruples** the friction tax, matching front-office reality: supermax deals on apron teams create extreme roster paralysis.

---

## 6. Net Surplus Value ($NSV$) & Roster-Wide Deltas

$$NSV_i = GSV_i - \text{Friction}_i$$

### The Roster-Wide Bracket Shift Externality
Because bracket state is a franchise property, transactions alter the friction of the **entire roster**:

$$\Delta NSV_{\text{Team}} = \sum_{k \in \text{Roster}_{\text{post}}} NSV_k(T_{\text{post}}) - \sum_{k \in \text{Roster}_{\text{pre}}} NSV_k(T_{\text{pre}})$$

If a trade sheds $\$5\text{M}$ and drops a team from **Bracket 3 (Second Apron)** into **Bracket 2 (First Apron)**:
- $\lambda$ on *every single player* remaining on the roster drops from $0.70$ to $0.35$.
- This unlocks **Friction Drag Relief**, incentivizing teams to escape the Second Apron even when sacrificing on-court talent.

---

## 7. Parameter Sensitivity Analysis, Talent Frontier & League Scan

The model provides formal sensitivity and generalization tools in [`boardman/sensitivity.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/sensitivity.py):

### A. True 2D Sensitivity Grid (`analyze_trade_sensitivity`)
Evaluates trade surplus swings across a 2D parameter grid of $\lambda$ scale ($0.0\times$ to $2.0\times$) and Cost-Per-Win ($C_w \in [\$3.5\text{M}, \$6.5\text{M}]$).
- At $\lambda = 0.00$, $\Delta NSV$ strictly collapses to the linear $/WAR result ($-\$10.53\text{M}$).
- As $\lambda$ increases, $\Delta NSV$ grows monotonically, turning positive at about $0.66\times$ baseline ($\lambda_3 \approx 0.46$ **with $\lambda_2 \approx 0.23$**, since every bracket scales together). This is not the same quantity as the fixed-$\lambda_2$ break-even below.

### B. Break-Even λ₃ (`calculate_break_even_lambda_3`) & Scenario Simulation (`calculate_headline_uncertainty`)
Holding $\lambda_2 = 0.35$ fixed, $\Delta NSV$ is linear in $\lambda_3$ for a Bracket 3 → 2 escape, so the break-even is solved exactly from two engine evaluations:
- **Required friction relief:** $\$10.53\text{M}$/yr (the linear $/WAR deficit)
- **Break-even:** $\lambda_3 \ge 0.58$ (single-season WAR); $\lambda_3 \ge 0.78$ under the multi-season WAR prior, above the 0.70 baseline

The scenario simulation draws an *assumed* $\lambda_3 \sim \text{Uniform}(0.40, 0.85)$ and WAR noise $\sim \text{Normal}(0, 0.35)$ over 10,000 trials:
- **Share of scenarios net-positive:** $60.2\%$
- **Mean scenario $\Delta NSV$:** $+\$2.04\text{M}$
- **90% scenario interval:** $[-\$7.37\text{M}, +\$11.55\text{M}]$

This is not a posterior or credible interval. The interval straddles zero, and the 60% largely restates where 0.58 sits in the assumed range.

### C. The Apron Escape Frontier: Allowable Talent Sacrifice Curve (`calculate_apron_escape_frontier`)
Under linear $/WAR, shedding $\$5.0\text{M}$ in salary allows a team to tolerate losing at most:
$$\Delta W_{\text{linear}} = -\frac{S_{\text{shed}}}{C_w} = -\frac{\$5.0\text{M}}{\$5.23\text{M}} = -0.96 \text{ WAR}$$
Under the **Apron Friction Model** at baseline $\lambda_3 = 0.70$, dropping below the Second Apron unlocks **$+\$15.93\text{M}$ in friction relief**, expanding the allowable talent sacrifice to:
$$\Delta W_{\text{apron}} = -\frac{\$5.0\text{M} + \$15.93\text{M}}{\$5.23\text{M}} = -3.93 \text{ WAR}$$
This represents a **4.1x expansion in tolerable on-court talent loss**, explaining why real front offices execute salary dumps that look disastrous under linear metrics.

### D. Cleveland Second Apron Escape Menu (`scan_apron_escape_trades`)
If escaping the Second Apron is worth $R$/yr to Cleveland, any trade that sheds at least $3.86M and costs less than $R / C_w$ WAR is net-positive, whereas linear $/WAR models reject every talent sacrifice. At the baseline scenario, $R = +\$15.93\text{M}$ (~3.05 WAR). The scan ranks Cleveland's legal 1-for-1 escapes by $\Delta NSV$. It defaults to the multi-season WAR prior (`metric_col="war_projected"`) and excludes the team's top three players by that prior (`protect_top_n=3`: Mitchell, Harden, Mobley), so it does not recommend trading the franchise core.

### E. League Ranking Elasticity (`calculate_ranking_elasticity`)
Quantifies how player contract rankings diverge between linear ($GSV$) and apron ($NSV$) models:
- **Evan Mobley (CLE, $46.4M):** Linear Rank = 97th $\to$ Apron Rank = 138th (**$-41$ spots**, $-\$9.74\text{M}$ friction).
- **Donovan Mitchell (CLE, $46.4M):** Linear Rank = 24th $\to$ Apron Rank = 43rd (**$-19$ spots**, $-\$9.74\text{M}$ friction).
- **Karl-Anthony Towns (NYK, $53.1M):** Linear Rank = 91st $\to$ Apron Rank = 119th (**$-28$ spots**, $-\$6.39\text{M}$ friction).

---

## 8. Empirical Tests & Econometric Discontinuity Evidence

$\lambda$ is a scenario input from the statutory cost breakdown in `config.py`. We test it against real NBA transactions and multi-season payroll data:

### A. Can Salary Dumps Identify $\lambda_3$? (No)
When a contender sacrifices draft equity $E$ to shed salary $S$ with zero incoming salary, it saves $S$ in salary and $T_{\text{tax}}$ in luxury tax, and gives up $E$ plus lost win production ($\Delta W \times C_w$). The trade is rational if and only if:
$$\Delta \text{Friction Relief} \ge E - S - T_{\text{tax}} + (\Delta W \times C_w)$$

In the Denver Nuggets / Reggie Jackson transaction (June 27, 2024), Denver surrendered $3$ second-round draft picks ($\approx \$8.0\text{M}$ in surplus equity) to dump Reggie Jackson's $\$5.25\text{M}$ contract to Charlotte for zero incoming salary:
- **Decision-Time vs. Realized Context:** At decision time, pre-free agency projections positioned Denver at ~$\$193.0\text{M}$ (~$\$4.1\text{M}$ over the Second Apron of $\$188.93\text{M}$, assuming Kentavious Caldwell-Pope was retained). Subsequently, KCP left in free agency, leaving realized payroll at $\$182.57\text{M}$ (or $\$187.82\text{M}$ with Jackson, $\$1.1\text{M}$ below the apron).
- **Costs and Savings:** $E \approx \$8.0\text{M}$, $S = \$5.25\text{M}$ (pre-tax net cost $\$2.75\text{M}$), and $T_{\text{tax}} \approx \$14.3\text{M}$ from the 2023 CBA incremental tax schedule (`calculate_luxury_tax`, non-repeater rates, realized payroll; $\approx \$17.8\text{M}$ on the decision-time payroll). Net cost after tax $\approx -\$11.5\text{M}$.
- Across Denver's 2024–25 quadratic roster bases ($B_{\text{pre}} = \$42.25\text{M}, B_{\text{post}} = \$42.05\text{M}$):
  $$\lambda_3 \ge \frac{E - S - T_{\text{tax}} + \Delta W \cdot C_w + 0.35 \times B_{\text{post}}}{B_{\text{pre}}} \ge \mathbf{0.08} \quad (\text{or } \mathbf{0.14} \text{ if Jackson cost } 0.5\text{ WAR})$$
- **Non-binding:** both bounds are below $\lambda_2 = 0.35$. Tax cash alone justifies the dump, so deep-tax salary dumps cannot separate operational friction from tax savings. (An earlier version dropped $T_{\text{tax}}$ and reported $\lambda_3 \ge 0.41$.)

### B. Econometric Payroll Bunching, Placebo Controls & Statistical Power (2020–2026)
Analyzing all 180 team-seasons across 2020–2026 reveals:
- **Second Apron Bunching:** Post-2023 NBA payrolls exhibit suggestive bunching immediately below the Second Apron (6 team-seasons in the $-\$5\text{M}$ to $\$0$ band: NYK $-\$0.37\text{M}$, GSW $-\$3.70\text{M}$, LAL $-\$0.91\text{M}$, MIL $-\$0.57\text{M}$).
- **Synthetic Placebo Line & Fisher Exact Test:** Because the Second Apron did not exist prior to the 2023 CBA, the pre-2023 line is an explicit synthetic placebo comparison. A two-sided Fisher Exact Test yields $p \approx 0.50$ (ratio within $\pm\$5\text{M}$ yields $p = 1.00$). We report candidly that at $N=90$ post-CBA team-seasons, Second Apron bunching is statistically underpowered.
- **Verified Luxury Tax Bunching:** In contrast, the Luxury Tax threshold has existed across both eras. Within $\pm\$3\text{M}$ of the tax line, teams bunch heavily below rather than above:
  - *Pre-CBA (2020–2023):* **24 below vs. 1 above**
  - *Post-CBA (2023–2026):* **23 below vs. 6 above**
  - This confirms that NBA front offices demonstrably respond to statutory financial cliffs when penalties bite.
- **Second Apron Contender Attrition:** Teams above the Second Apron collapsed from 4 in 2023–24 to 3 in 2024–25 to **only 1 team (Cleveland)** in 2025–26 ($-75\%$ attrition).

---

## 9. Model Limitations, Blended Priors & Data Provenance

1. **Temporal Scope:** All contracts, roster models, and apron evaluations analyze the **2025–26 NBA season** (with 2026–27 currently underway).
2. **Single-Season Box-Score Scope vs. Multi-Season Prior:** Single-season box scores naturally penalize injured stars (e.g. Tyrese Haliburton, Jayson Tatum during injury stints). To address this, `boardman` adopts a **Multi-Season Blended WAR Prior (`war_projected`)** as the primary default impact metric, which regresses single-season box scores against 3-year historical baselines (Marcel-style weighted regression approach). Under this model, Tatum and Haliburton are recognized as positive star assets, and underwater contracts like Zach LaVine, Khris Middleton, and Jordan Poole correctly occupy the bottom ranks.
3. **Draft Pick Equity Valuation:** The engine models forfeited draft picks using empirical draft-value curves (~$11.5M average rookie contract surplus), but does not account for team-specific lottery protections or standings variance.
4. **Dead Money Directional Resolution:**
   - *Damian Lillard:* Milwaukee waived and stretched Lillard ($\$22.5\text{M}$ dead money on MIL); Portland signed him on an active contract ($\$14.1\text{M}$ active roster on POR). In our engine, MIL Lillard is strictly flagged as `is_dead_money = True`, whereas POR Lillard is active roster (`is_dead_money = False`).
   - *Deandre Ayton:* Portland waived and stretched Ayton ($\$25.5\text{M}$ dead money on POR); Lakers hold his active deal ($\$8.1\text{M}$ on LAL).
   - Dead-money contracts are strictly prohibited from being traded in `boardman/trade_engine.py`.
5. **Data Provenance:** Team payroll figures reconcile exactly to the sum of player contracts in our scraped dataset within $\pm0.0\%$ (internal consistency verification).

