# 2023 CBA Trade Matching & Apron Restriction Rules

This document details the statutory trade rules enforced by [`boardman/cba_rules.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/cba_rules.py) under the 2023 NBA Collective Bargaining Agreement (CBA).

---

## 1. Statutory Thresholds (2025–26 Season)

| Threshold | Official Amount | Description |
| :--- | :---: | :--- |
| **Salary Cap** | **$\$154,647,000$** | Base threshold for cap space and exception calculations. |
| **Luxury Tax Line** | **$\$187,895,000$** | Threshold triggering dollar-for-dollar cash tax payments. |
| **First Apron** | **$\$195,945,000$** | Hard 100% salary matching ceiling; triggers hard-caps. |
| **Second Apron** | **$\$207,824,000$** | Aggregation bans, frozen picks, and zero-cash rules. |

---

## 2. Non-Taxpayer Matching Bands (Sub-Tax Teams) & Statutory Escalation

Under **Article VII, Section 6(j) of the 2023 CBA**, trade matching band thresholds and minimum cash buffers do not remain static. Instead, they escalate annually in direct proportion to the growth of the League Salary Cap from the 2023–24 baseline:

$$\text{Escalation Factor} = \frac{\text{Salary Cap}_{2025\text{--}26}}{\text{Salary Cap}_{2023\text{--}24}} = \frac{\$154,647,000}{\$136,021,000} \approx 1.136934298$$

For teams whose post-trade payroll remains strictly below the **First Apron**, allowable incoming salary ($S_{\text{in}}$) is calculated based on total outgoing salary ($S_{\text{out}}$) using these statutory escalated bands:

### Band 1: Outgoing Salary $\le \$8,527,011$
$$S_{\text{in}} \le (200\% \times S_{\text{out}}) + \$284,234$$
*(Escalated from the baseline $\$7,500,000$ and $\$250,000$ buffer).*

*Example:* A team trading a $\$4,000,000$ player can receive up to:
$$(2.00 \times 4.0\text{M}) + 0.284\text{M} = \$8,284,234$$

### Band 2: $\$8,527,011 < \text{Outgoing Salary} \le \$32,971,107$
$$S_{\text{in}} \le S_{\text{out}} + \$8,527,011$$
*(Escalated from the baseline $\$7,500,000$ and $\$29,000,000$ threshold).*

*Example:* A team trading a $\$15,000,000$ player can receive up to:
$$15.0\text{M} + 8.527\text{M} = \$23,527,011$$

### Band 3: Outgoing Salary $> \$32,971,107$
$$S_{\text{in}} \le (125\% \times S_{\text{out}}) + \$284,234$$

*Example:* A team trading a $\$35,000,000$ player can receive up to:
$$(1.25 \times 35.0\text{M}) + 0.284\text{M} = \$44,034,234$$

---

## 3. The First Apron Hard-Cap Clamp

Under 2023 CBA rules, a non-taxpayer **cannot** use non-taxpayer percentage matching bands to jump past the First Apron.

If taking back the standard allowable incoming salary would push the team's post-trade payroll past **$\$195,945,000$**, the incoming salary is clamped to the available apron slack:

$$\text{Max Allowable Incoming} = \min\Big(\text{Band Max}, \text{First Apron} - (\text{Payroll}_{\text{pre}} - S_{\text{out}})\Big)$$

*A team can always take back at least $100\%$ of outgoing salary if they already match.*

---

## 4. First Apron Matching Rules

Franchises whose payroll sits between the Luxury Tax and First Apron (or are pushed into the First Apron):

1. **100% Hard Matching Rule:**
   $$S_{\text{in}} \le S_{\text{out}}$$
   *(The team cannot take back even $\$1$ more than they send out).*
2. **Traded Player Exception (TPE) Restrictions:** Pre-existing TPEs generated in prior transactions cannot be used to absorb salary if the absorption would leave the team above the First Apron.
3. **Loss of Bi-Annual Exception:** The Bi-Annual Exception cannot be used.

---

## 5. Second Apron Prohibitions (The Deep Freeze)

Franchises whose payroll exceeds the Second Apron (**$\$207,824,000$**) face the most severe operational constraints in modern sports governance:

### A. Zero Salary Aggregation Rule
A Second Apron team **cannot aggregate** multiple outgoing players to acquire a single incoming player whose salary exceeds any individual outgoing player's salary:

$$\forall p_{\text{in}} \in \text{Incoming}, \quad \text{Salary}(p_{\text{in}}) \le \max_{p_{\text{out}} \in \text{Outgoing}} \text{Salary}(p_{\text{out}})$$

*Illegal Example:*
- Team sends: Player A ($\$16\text{M}$) + Player B ($\$14\text{M}$) = $\$30\text{M}$ total outgoing.
- Team attempts to acquire: Player C ($\$28\text{M}$).
- **Verdict: ILLEGAL.** Player C ($\$28\text{M}$) exceeds the highest single outgoing salary ($\$16\text{M}$).

### B. Zero Outgoing Cash Rule
Second Apron teams are **strictly prohibited from sending outgoing cash** in any trade:

$$\text{Cash}_{\text{out}} = \$0$$

### C. Draft Pick Freezing & Demotion
- A franchise above the Second Apron cannot trade their first-round pick **seven years in the future** (the pick is frozen).
- If the franchise remains in the Second Apron in two of the subsequent four seasons, that frozen pick is automatically moved to the **30th and final pick of the first round**, regardless of regular season record.

---

## 6. Compliance Engine Architecture in `boardman`

The [`check_trade_compliance`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/cba_rules.py#L60) function returns a typed [`TradeComplianceCheck`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/cba_rules.py#L17) model tracking:
- `is_salary_matching_valid`
- `is_aggregation_valid`
- `is_cash_valid`
- `is_hard_cap_respected`
- `violations: list[str]` (human-readable statutory citations)
