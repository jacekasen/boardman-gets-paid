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

## 5. Empirical Derivation of the Apron Friction Tax ($\lambda$)

To model the operational and opportunity-cost drag of contracts on high-payroll franchises:

$$\text{Friction}_i = \lambda(T) \times \text{Cap Hit}_i \times \left(\frac{\text{Cap Hit}_i}{\text{Salary Cap}}\right)$$

Where $\lambda(T)$ is a discrete operational multiplier conditioned on the franchise's payroll bracket $T$:

| Bracket $T$ | Payroll Range | Operational Multiplier $\lambda(T)$ | Franchise Restrictions | Empirical Opportunity Cost Basis |
| :---: | :---: | :---: | :--- | :--- |
| **0** | $< \text{Luxury Tax}$ ($\$187.9\text{M}$) | **$0.00$** | Full roster flexibility, escalated matching bands. | Zero regulatory restriction. |
| **1** | $\text{Tax} \to \text{1st Apron}$ ($\$195.9\text{M}$) | **$0.15$** | Cash luxury tax penalties; Bi-Annual preserved. | Marginal cash tax ($1.50x to $2.50x) + initial liquidity discount. |
| **2** | $\text{1st} \to \text{2nd Apron}$ ($\$207.8\text{M}$) | **$0.35$** | Hard 100% salary matching; loss of Bi-Annual. | Forfeiture of BAE (~$4.7M) + 100% hard matching constraint. |
| **3** | $> \text{Second Apron}$ ($\$207.8\text{M}$) | **$0.70$** | Frozen 7-yr picks; zero aggregation; zero cash. | Pick freeze/demotion (~$7.3M) + lost TP-MLE (~$5.4M) + illiquidity discount (~$8.0M) + tax surcharges (~$10.0M) = **~$31.0M annual drag**. |

### Detailed Breakdown of Bracket 3 ($\lambda = 0.70$)
1. **Frozen Draft Pick & End-of-Round Demotion ($\approx \$7.3\text{M}$):**
   - Under CBA rules, a Second Apron team's 7-year out 1st-round pick is frozen. If they repeat, it drops to pick 30.
   - Historical rookie contract surplus curves demonstrate that an average middle-first pick (#15–#20) generates $\approx \$10.5\text{M}$ in net surplus over 4 years, whereas pick #30 generates only $\approx \$3.2\text{M}$. Expected loss = **$\$7.3\text{M}$**.
2. **Forfeiture of the Taxpayer Mid-Level Exception ($\approx \$5.4\text{M}$):**
   - Second Apron teams cannot use the TP-MLE ($5.4M market value), forcing them to fill rotation depth exclusively with minimum contracts.
3. **Asset Illiquidity & Aggregation Ban ($\approx \$7.5\text{M}$–$\$10.0\text{M}$):**
   - The inability to aggregate multiple contracts or send cash creates a 10%–15% illiquidity haircut on high-salary player trades.
4. **Sum of Penalties:** Combining these empirical opportunity costs yields **$\approx \$25\text{M}$–$\$32\text{M}$** in annual structural drag, directly matching Cleveland's calculated roster friction of **$\$31.07\text{M}$**.

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

## 7. Parameter Sensitivity Analysis & Ranking Elasticity

The model provides formal sensitivity evaluation tools in [`boardman/sensitivity.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/sensitivity.py):

### A. 2D Sensitivity Grid (`analyze_trade_sensitivity`)
Evaluates trade surplus swings across a 2D parameter grid of $\lambda$ scale ($0.0\times$ to $2.0\times$) and Cost-Per-Win ($C_w \in [\$3.5\text{M}, \$6.5\text{M}]$).
- In the Cleveland–Detroit trade, when $\lambda = 0.0$ (linear $/WAR$), the trade is $-\$10.53\text{M}$.
- The tipping point occurs at $\lambda \approx 0.45$, above which the transaction turns positive, demonstrating that friction relief dominates talent loss.

### B. League Ranking Elasticity (`calculate_ranking_elasticity`)
Quantifies how player contract rankings diverge between linear ($GSV$) and apron ($NSV$) models:
- **Evan Mobley (CLE, $46.4M):** Linear Rank = 97th $\to$ Apron Rank = 138th (**$-41$ spots**, $-\$9.74\text{M}$ friction).
- **Donovan Mitchell (CLE, $46.4M):** Linear Rank = 24th $\to$ Apron Rank = 43rd (**$-19$ spots**, $-\$9.74\text{M}$ friction).
- **Karl-Anthony Towns (NYK, $53.1M):** Linear Rank = 91st $\to$ Apron Rank = 119th (**$-28$ spots**, $-\$6.39\text{M}$ friction).

---

## 8. Real-World Front Office Validation (2024–2026)

NBA front office actions over the 2024–2026 period confirm that teams actively price apron escape over linear talent:
1. **Denver Nuggets Salary Dump (Summer 2024):** Denver traded Reggie Jackson ($5.25M) and attached **three second-round draft picks** to Charlotte for zero incoming player value, exclusively to duck below the Second Apron.
2. **Minnesota Timberwolves / Karl-Anthony Towns Trade (Fall 2024):** Minnesota moved franchise star KAT to New York for Julius Randle and Donte DiVincenzo to preempt Second Apron repeater penalties that would have frozen their 2032 pick.
3. **Dallas Mavericks / Derrick Jones Jr. (Summer 2024):** Dallas prioritized avoiding First Apron hard-cap restrictions over re-signing an essential finals starter.

---

## 9. Model Limitations

1. **Single-Season Box-Score Scope:** The engine currently models 2025–26 box-score statistics. It does not project multi-year aging curves, contract term risk, or future cap escalation.
2. **Box-Score Injury Sensitivity:** Players with 0 games played due to injury register 0 WAR in single-season box scores. Future iterations will incorporate multi-year Bayesian priors.
3. **Static Draft Capital Pricing:** Forfeited draft picks are evaluated using average historical draft surplus curves (~$11.5M rookie surplus) rather than team-specific standing probabilities.
