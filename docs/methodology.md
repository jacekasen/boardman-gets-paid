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

## 5. The Apron Friction Tax ($\lambda$)

To model the operational and opportunity-cost drag of contracts on high-payroll franchises:

$$\text{Friction}_i = \lambda(T) \times \text{Cap Hit}_i \times \left(\frac{\text{Cap Hit}_i}{\text{Salary Cap}}\right)$$

Where $\lambda(T)$ is a discrete operational multiplier conditioned on the franchise's payroll bracket $T$:

| Bracket $T$ | Payroll Range | Operational Multiplier $\lambda(T)$ | Franchise Restrictions |
| :---: | :---: | :---: | :--- |
| **0** | $< \text{Luxury Tax}$ ($\$187.9\text{M}$) | **$0.00$** | Full roster flexibility, sub-tax matching bands. |
| **1** | $\text{Tax} \to \text{1st Apron}$ ($\$195.9\text{M}$) | **$0.15$** | Cash luxury tax penalties; Bi-Annual exception preserved. |
| **2** | $\text{1st} \to \text{2nd Apron}$ ($\$207.8\text{M}$) | **$0.35$** | Hard 100% salary matching; loss of Bi-Annual exception. |
| **3** | $> \text{Second Apron}$ ($\$207.8\text{M}$) | **$0.70$** | Frozen 7-yr draft picks; no salary aggregation; no outgoing cash. |

### Quadratic Drag Property
Notice the quadratic term:

$$\text{Cap Hit}_i \times \frac{\text{Cap Hit}_i}{\text{Salary Cap}} = \frac{(\text{Cap Hit}_i)^2}{\text{Salary Cap}}$$

- A **$\$20\text{M}$ starter** in Bracket 3 pays:
  $$\text{Friction} = 0.70 \times 20\text{M} \times \frac{20\text{M}}{154.6\text{M}} \approx \$1.81\text{M}$$
- A **$\$40\text{M}$ supermax** in Bracket 3 pays:
  $$\text{Friction} = 0.70 \times 40\text{M} \times \frac{40\text{M}}{154.6\text{M}} \approx \$7.24\text{M}$$

Doubling the contract size **quadruples** the friction tax. This matches front-office reality: mega-contracts on apron teams create extreme roster immobility.

---

## 6. Net Surplus Value ($NSV$) & Roster-Wide Deltas

$$NSV_i = GSV_i - \text{Friction}_i$$

### The Roster-Wide Bracket Shift Externality
Because bracket state is a franchise property, transactions alter the friction of the **entire roster**:

$$\Delta NSV_{\text{Team}} = \sum_{k \in \text{Roster}_{\text{post}}} NSV_k(T_{\text{post}}) - \sum_{k \in \text{Roster}_{\text{pre}}} NSV_k(T_{\text{pre}})$$

If a trade sheds $\$5\text{M}$ and drops a team from **Bracket 3 (Second Apron)** into **Bracket 2 (First Apron)**:
- $\lambda$ on *every single player* remaining on the roster drops from $0.70$ to $0.35$.
- This unlocks millions of dollars in **Friction Drag Relief**, incentivizing teams to escape the Second Apron even when trading talent.

---

## 7. Shadow Compensation ("The Uncle Dennis Parameter")

In light of the September 2026 Kawhi Leonard / Los Angeles Clippers cap circumvention investigation, the engine incorporates an optional shadow compensation parameter:

$$\text{Effective Cost}_i = \text{Cap Hit}_i + \text{Off-Cap Cash}_i$$

$$GSV_i = FV_i - \text{Effective Cost}_i$$

This allows analysts to model the true economic investment and surplus erosion of under-the-table sponsorships and off-the-cap benefits.
