# Valuation Methodology & Data Architecture

`boardman-gets-paid` prices NBA player contracts against modern Collective Bargaining Agreement (CBA) constraints to identify contract efficiency and surplus-value arbitrage anomalies.

---

## 1. Production Metrics & Multi-Season Talent Prior

To maintain transparency and full open-source reproducibility without relying on proprietary or paywalled metrics, the engine standardizes publicly available box-score impact metrics:

### A. Value Over Replacement Player (VORP)
VORP measures a player's box-score impact relative to a replacement-level baseline ($-2.0$ Box Plus/Minus), weighted by team minutes and normalized to an 82-game schedule:

$$\text{VORP} = \left[\text{BPM} - (-2.0)\right] \times \left(\frac{\% \text{ of team minutes}}{100}\right) \times \left(\frac{\text{team games}}{82}\right)$$

### B. Wins Above Replacement Conversion ($\hat{W}_{\text{VORP}}$)
Based on empirical historical regressions across NBA box-score metrics:

$$\hat{W}_{\text{VORP}} = 2.70 \times \text{VORP}$$

### C. Multi-Season Talent Baseline (`war_projected`)
Single-season box scores are vulnerable to noise, small sample sizes, and mid-season injuries. To establish an economically defensible measure of player talent, the default metric incorporates a multi-season Marcel-style regression:

1. **Historical Prior:** Weights the player's performance across preceding seasons (60% weight on 2024–25, 40% on 2023–24).
2. **Talent Blend:** For players active in the current snapshot, regresses realized production toward their talent prior:
   $$\hat{W}_{\text{projected}} = 0.65 \times \hat{W}_{\text{VORP}} + 0.35 \times \text{Prior}$$
3. **Injury Discount:** For injured players with zero regular-season minutes, applies a 25% injury shrinkage discount against their historical baseline.
4. **Dead Money Enforcement:** Waived, stretched, and prior-stint historical contract obligations are strictly assigned **0.00 WAR** across all proxies.

---

## 2. Open-Market Cost Per Win Calibration ($C_w$)

In standard surplus models, pooling rookie-scale contracts (such as Victor Wembanyama producing superstar WAR on a $13.4M salary) severely distorts the market price of a win.

To prevent this distortion, `boardman-gets-paid` calibrates $C_w$ exclusively on **unconstrained veteran contracts** (contracts $\ge \$5.0\text{M}$ with positive WAR, excluding dead money and unverified salaries):

$$C_w = \frac{\sum_{j \in \text{Veterans}} \text{Cap Hit}_j}{\sum_{j \in \text{Veterans}} \hat{W}_j}$$

For the 2025–26 NBA season snapshot:
- **Baseline Cost Per Win ($C_w$):** **$\$5,193,442.76$** per win above replacement.
- This represents what NBA franchises pay in the open veteran market to acquire one marginal win above replacement level.

---

## 3. Fair Production Value ($FV$) & Net Surplus ($NSV$)

Using the calibrated cost per win:

$$\text{Fair Production Value } (FV_i) = \hat{W}_i \times C_w$$

$$\text{Gross Surplus Value } (GSV_i) = FV_i - \text{Cap Hit}_i$$

- **Positive Surplus:** Indicates a high-efficiency contract (production exceeds cap allocation).
- **Negative Surplus:** Indicates a franchise anchor (cap allocation exceeds on-court contribution).

### The Apron Friction Drag ($\lambda$)
For high-payroll franchises above the luxury tax aprons, contracts impose operational illiquidity and regulatory penalties (frozen draft picks, loss of the mid-level exception, and trade-aggregation bans). The engine applies a quadratic friction drag:

$$\text{Friction}_i = \lambda(T) \times \text{Cap Hit}_i \times \left(\frac{\text{Cap Hit}_i}{\text{Salary Cap}}\right)$$

$$\text{Net Surplus Value } (NSV_i) = GSV_i - \text{Friction}_i$$

Where $\lambda(T)$ is conditioned on the franchise's payroll bracket:
- **Bracket 0 ($< \text{Tax}$):** $\lambda = 0.00$ *(Full roster mobility)*
- **Bracket 1 ($\text{Tax} \to \text{1st Apron}$):** $\lambda = 0.15$ *(Cash luxury tax drag)*
- **Bracket 2 ($\text{1st} \to \text{2nd Apron}$):** $\lambda = 0.35$ *(Hard matching constraint)*
- **Bracket 3 ($> \text{2nd Apron}$):** $\lambda = 0.70$ *(Second apron operational bans)*

---

## 4. ROI Efficiency Multiple

To compare contract value on a normalized dollar-for-dollar basis, the engine calculates the **ROI Multiple**:

$$\text{ROI Multiple} = \frac{FV_i}{\text{Cap Hit}_i}$$

- **ROI > 1.0x:** Positive economic return (e.g. Victor Wembanyama at **5.36x**, Chet Holmgren at **4.12x**, Nikola Jokić at **2.42x**).
- **ROI < 1.0x:** Negative return / underwater contract (e.g. Zach LaVine at **0.22x**, Paul George at **0.35x**).
- **Two-Way / Unknown:** Displays as `N/A` (never divided by zero or treated as infinite ROI).

---

## 5. Contract Tier Taxonomy

Contracts in the 2025–26 dataset are classified into five explicit categories:
1. **Rookie Scale:** Entry-level contracts under statutory rookie scales (experience $\le 4$ seasons, salary $\le \$16\text{M}$).
2. **Max / Supermax:** Franchise cornerstone contracts ($\ge \$35\text{M}$ AAV or $\ge 22\%$ cap share).
3. **Mid-Level:** Core rotation veterans ($\$8\text{M}$ to $\$35\text{M}$).
4. **Minimum / Rotation:** Value contributors ($< \$8\text{M}$).
5. **Two-Way / Unknown:** Non-guaranteed or mid-season unverified cap allocations.

---

## 6. Data Integrity & Verification

1. **Stint Deduplication:** Players traded across multiple teams in 2025–26 (e.g. Kyle Anderson, Charles Bassey, Rayan Rupert) have their active roster status assigned strictly to their **latest regular-season stint team**.
2. **Dead Money Zeroing:** Historical obligations and waived contracts remain on team payroll books for cap accounting, but are guaranteed to have **0.00 WAR** so they cannot inflate team production.
3. **Zero Active Duplicates:** Tested by automated regression suite—no player in the NBA has duplicate active roster records.
4. **Packaged Reproducibility:** Sourced from local raw files committed in `data/raw/`, allowing complete offline re-ingestion and validation.
