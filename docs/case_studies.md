# Real-World Case Studies & Empirical Benchmarks

This document reviews the benchmark case studies implemented in [`boardman/case_studies.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/case_studies.py) and featured in the interactive Streamlit application.

---

## Flagship Case Studies: The Apron Escape Pair

> **Core Research Question:** *What does the `boardman-gets-paid` model conclude that a linear Dollar-per-WAR model gets completely wrong?*

Rather than relying on a single transaction whose verdict flips depending on single-season injury variance, `boardman` presents a **Flagship Pair of Results** under our multi-season true-talent prior (`war_projected`):

### 1. 💎 Flagship 1: The Robust Second Apron Escape Flip (Cleveland ↔ Dallas)
- **The Trade:** Cleveland ($211.7M payroll, Bracket 3 / Second Apron) trades **Max Strus** ($15.94M cap hit, 1.10 WAR) to Dallas for **Caleb Martin** ($9.59M cap hit, -0.23 WAR).
- **Salary Saved:** $+\$6,342,408$ (drops Cleveland's payroll to $\$205.3\text{M}$, **comfortably below the Second Apron of $\$207.8\text{M}$** into Bracket 2).
- **On-Court Talent Delta:** $-1.33$ WAR (Strus 1.10 $\to$ Martin -0.23).
- **Linear $/WAR Verdict:** ❌ **REJECT ($-\$613,322$ net deficit)**. Linear models reject because $1.33$ wins is valued at $\$6.96\text{M}$ against $\$6.34\text{M}$ in salary saved.
- **Roster-Wide Friction Relief:** **$+\$15,901,898$** (recovers operational mobility, unfreezes 2033 first-round draft pick).
- **Board Man Net Surplus Verdict:** ✅ **ACCEPT ($+\$15,288,576$ Net Surplus Gain)**.
- **Break-Even & Robustness:** Break-even requires $\lambda_3 \ge 0.356$ (holding $\lambda_2 = 0.35$ fixed). Because the linear deficit is only $\$613\text{K}$, this flip succeeds across **100% of scenarios** drawn from our 4 sourced statutory cost components!

---

### 2. ⚡ Flagship 2: The High-Stakes, Assumption-Dependent Flip (Cleveland ↔ Detroit)
- **The Trade:** Cleveland trades **Jarrett Allen** ($20.0M cap hit, 6.37 WAR) to Detroit for **Isaiah Stewart** ($15.0M cap hit, 1.70 WAR).
- **Salary Saved:** $+\$5,000,000$ (drops Cleveland to $\$206.7\text{M}$, below the Second Apron).
- **On-Court Talent Delta:** $-4.67$ WAR under multi-season true-talent baselines.
- **Linear $/WAR Verdict:** ❌ **REJECT ($-\$19,423,502$ net deficit)**.
- **Roster-Wide Friction Relief:** **$+\$15,931,490$**.
- **Board Man Net Surplus Verdict (baseline $\lambda_3 = 0.70$):** ❌ **REJECT ($-\$3,492,012$ net deficit)**.
- **The Insight:** Escaping the Second Apron cannot overcome a severe 4.67 WAR talent drop unless escaping is worth $\ge \$19.42\text{M}$/yr, requiring $\mathbf{\lambda_3 \ge 0.779}$ (win probability only ~3.4%). This illustrates a high-stakes organizational gamble on extreme friction severity.
*(Note: Under single-season box scores where Allen missed time, the linear deficit was only -$10.53M and the trade flipped at $\lambda_3 \ge 0.58$. `boardman` transparently exposes this assumption sensitivity.)*

---

### The Core Analytical Principle & Cleveland's Candidate Escape Ranking

> **The Fundamental Principle:** If escaping the Second Apron is worth $R$/yr to Cleveland, any trade that sheds at least $\$3.86\text{M}$ and costs less than $R / C_w$ WAR is net-positive, whereas linear $/WAR models reject every talent sacrifice. At the baseline scenario, $R = +\$15.93\text{M}$ (~3.05 WAR).

[`scan_apron_escape_trades`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/sensitivity.py) evaluates all legal 1-for-1 swaps across the league to provide Cleveland with an **apron escape ranking menu**, using the multi-season WAR prior and protecting Cleveland's top three players (Mitchell, Harden, Mobley):

| Cleveland Outgoing | Partner Franchise | Incoming Player | Salary Shed | On-Court WAR Loss | Linear $/WAR Verdict | Board Man Net Surplus |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **Max Strus** | CHI | Jaden Ivey | $\$5.8\text{M}$ | $-1.14$ WAR | $-\$0.1\text{M}$ | **$+\$15.7\text{M}$** |
| **Sam Merrill** | UTA | Kevin Love | $\$4.3\text{M}$ | $-1.14$ WAR | $-\$1.6\text{M}$ | **$+\$14.0\text{M}$** |
| **Jarrett Allen** | POR | Robert Williams | $\$6.7\text{M}$ | $-1.78$ WAR | $-\$2.6\text{M}$ | **$+\$13.4\text{M}$** |
| **Dennis Schröder** | WAS | Tre Johnson | $\$5.9\text{M}$ | $-2.78$ WAR | $-\$8.7\text{M}$ | **$+\$7.2\text{M}$** |

*Multi-season WAR prior (`war_projected`), baseline $\lambda_3 = 0.70$; 30 flips across 15 partner teams. Mitchell, Harden and Mobley are protected (`protect_top_n=3`).*

---

### The Theoretical Apron Escape Frontier

Under linear $/WAR, shedding $\$5.0\text{M}$ allows a team to tolerate losing at most:
$$\Delta W_{\text{linear}} = -\frac{S_{\text{shed}}}{C_w} = -\frac{\$5.0\text{M}}{\$5.23\text{M}} = -0.96 \text{ WAR}$$

Under the **Board Man Apron Friction Model** at baseline $\lambda_3 = 0.70$, dropping below the Second Apron unlocks **$+\$15.93\text{M}$ in friction relief**, expanding the allowable talent sacrifice to:
$$\Delta W_{\text{apron}} = -\frac{\$5.0\text{M} + \$15.93\text{M}}{\$5.23\text{M}} = -3.93 \text{ WAR}$$

This represents a **4.1x expansion in tolerable on-court talent loss** at the baseline scenario.

---

## Real-World Empirical Benchmarks: Salary Dumps, Placebos & Apron Discontinuity

### 1. Denver Nuggets / Reggie Jackson Salary Dump (June 27, 2024)
- **Context:** At the June 27, 2024 decision time, pre-free agency projections positioned Denver at ~$\$193.0\text{M}$ (~$\$4.1\text{M}$ over the Second Apron of $\$188.93\text{M}$, assuming Kentavious Caldwell-Pope was retained). Subsequently, KCP left in free agency, leaving realized end-of-season payroll at $\$182.57\text{M}$ (or $\$187.82\text{M}$ with Jackson, $\$1.1\text{M}$ below the apron).
- **The Transaction:** Denver sent Reggie Jackson ($\$5,250,000$) and **three second-round draft picks** (2025, 2029, 2030) to Charlotte for $\$0$ in incoming salary.
- **Costs and Savings:** 3 second-round picks ($E \approx \$8.0\text{M}$) against $S = \$5.25\text{M}$ salary saved (pre-tax net cost $\$2.75\text{M}$) **and** $T_{\text{tax}} \approx \$14.3\text{M}$ in luxury tax saved (2023 CBA incremental schedule, non-repeater rates, realized payroll). Net cost after tax $\approx -\$11.5\text{M}$.
- **Revealed-Preference Bound:** Across Denver's 2024–25 quadratic roster bases ($B_{\text{pre}} = \$42.25\text{M}, B_{\text{post}} = \$42.05\text{M}$):
  $$\lambda_3 \ge \frac{E - S - T_{\text{tax}} + \Delta W \cdot C_w + 0.35 \times B_{\text{post}}}{B_{\text{pre}}} \ge \mathbf{0.08} \quad (\text{or } \mathbf{0.14} \text{ if Jackson cost } 0.5\text{ WAR})$$
- **Non-binding:** both are below $\lambda_2 = 0.35$. Tax cash alone justifies the dump, so it does not identify $\lambda_3$. Second Apron friction has to be judged against the statutory cost breakdown instead. (An earlier version omitted $T_{\text{tax}}$ and reported $\lambda_3 \ge 0.41$.)

### 2. Multi-Season Econometric Payroll Bunching, Placebo Controls & Statistical Power (2020–2026)
Analyzing 180 team-seasons across 2020–2026 reveals:
- **Second Apron Bunching:** Post-2023 NBA payrolls exhibit suggestive bunching immediately below the Second Apron (6 team-seasons in the $-\$5\text{M}$ to $\$0$ band: NYK $-\$0.37\text{M}$, GSW $-\$3.70\text{M}$, LAL $-\$0.91\text{M}$, MIL $-\$0.57\text{M}$).
- **Synthetic Placebo Comparison & Fisher Exact Test:** Because the Second Apron did not exist prior to 2023, the pre-2023 curve is an explicit synthetic placebo line. A two-sided Fisher Exact Test yields $p \approx 0.50$ (ratio within $\pm\$5\text{M}$ yields $p = 1.00$), acknowledging that at $N=90$ team-seasons post-CBA, Second Apron bunching is statistically underpowered.
- **Verified Luxury Tax Bunching:** In contrast, the Luxury Tax threshold has existed across both eras. Within $\pm\$3\text{M}$ of the tax line, teams bunch heavily below rather than above:
  - *Pre-CBA (2020–2023):* **24 below vs. 1 above**
  - *Post-CBA (2023–2026):* **23 below vs. 6 above**
  - Proving that NBA front offices demonstrably avoid statutory tax cliffs when financial penalties bite.
- **Second Apron Contender Attrition:** Teams above the Second Apron collapsed from 4 in 2023–24 to 3 in 2024–25 to **only 1 team (Cleveland)** in 2025–26 ($-75\%$ attrition).


---

## Case Study 2: The Kawhi Leonard & LA Clippers Cap Circumvention Ruling (Sept 2026)

### Background & Investigative Reporting
In late 2025, investigative journalist Pablo Torre on *Pablo Torre Finds Out* broke reporting detailing off-the-books financial arrangements between the Los Angeles Clippers, superstar forward Kawhi Leonard, and his business representative Dennis Robertson ("Uncle Dennis").

Following extensive reporting, the NBA Board of Governors retained law firm Wachtell, Lipton, Rosen & Katz to conduct an independent inquiry. Our case study models the economic impact of shadow compensation and calculates the franchise's risk-adjusted penalty surface.

### The Scheme
- **The "No-Show" Endorsement Funnel:** The Clippers facilitated off-court income through team corporate sponsors. Most prominently, climate-fintech firm **Aspiration** signed Leonard to a reported **$28 million, 4-year contract** ($7.0M/yr) for zero verifiable deliverables.
- **Additional Sponsor Arrangements:** Reporting also highlighted arrangements with **Boingo Wireless** ($672,000 paid for a single one-hour meet-and-greet), **Daktronics**, and **Lockton Insurance**.
- **Uncle Dennis's Demands:** Robertson was identified as demanding and coordinating these off-the-cap benefits as a prerequisite for Leonard signing and remaining in Los Angeles.

### Historic NBA Sanctions (Hypothesized Regulatory Scenario)
1. **$30 Million Team Fine:** The largest fine allowable under league constitution precedents.
2. **Forfeiture of 5 First-Round Draft Picks:** Consecutive first-round picks in **2029, 2030, 2031, 2032, and 2033**.
   - Priced at $\$11.5\text{M}$ assumed rookie surplus curve value = **$\$57.5\text{M}$ in equity destroyed**.
3. **Executive Suspensions:**
   - **Steve Ballmer** (Owner): 1-year suspension.
   - **Gillian Zucker** (President of Business Ops): 1-year suspension.
   - **Lawrence Frank** (President of Basketball Ops): 6-month suspension.
4. **Dennis Robertson Banned:** 5-year league-wide ban from all NBA business.
5. **Kawhi Leonard Restitution:** Fined **$700,000** in restitution; cleared to be traded back to the Toronto Raptors.

### Modeling Risk-Adjusted Penalty & Shadow Compensation in `boardman`
In [`run_kawhi_circumvention_case_study`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/case_studies.py#L89):
- **On-the-Books Cap Hit:** $\$50,000,000$ (producing $14.31$ WAR).
- **Official Net Surplus ($NSV$):** **$+$\$24.8M**.
- **Shadow Cash Injection:** Adding $\$7,000,000$ annual Aspiration subsidy increases effective annual investment to $\$57,000,000$.
- **Circumvented Net Surplus:** **$+$\$17.8M** ($\$7.0\text{M}$ in immediate surplus erosion).
- **Risk-Adjusted Expected Penalty:**
  $$\mathbb{E}[\text{Penalty}] = P(\text{audit}) \times \Big[\text{Fine } (\$30\text{M}) + 5 \times \text{Draft Pick Equity } (\$57.5\text{M})\Big]$$
  *(Note: The $P(\text{audit}) = 0.30$ and $\$11.5\text{M}$/pick are exploratory parameter assumptions to illustrate the risk-adjusted penalty surface).*
  At $P(\text{audit}) = 0.30$, ownership incurs an expected sanction drag of **$\$26.25\text{M}$**, completely wiping out any surplus created by the contract.

**Primary Statutory & Investigative Sources:**
1. Pablo Torre, *Pablo Torre Finds Out* (Meadowlark Media, investigative reporting on Aspiration sponsorship).
2. Wachtell, Lipton, Rosen & Katz (Retained independent counsel for NBA Board of Governors).
3. NBA Constitution Article 35 & 2023 CBA Article XIII (*Salary Cap Circumvention & Unauthorized Agreements*).

---

## Case Study 3: The Cleveland Cavaliers Second Apron Aggregation Trap

### The Scenario
Cleveland ($211.7M payroll, Bracket 3, $\lambda = 0.70$) attempts to combine two veteran starters to acquire Boston guard Derrick White:
- **Cleveland Outgoing:** Max Strus ($\$15,936,452$) + Dennis Schröder ($\$14,104,000$) = **$\$30,040,452$**
- **Boston Outgoing:** Derrick White ($\$28,100,000$)

### Statutory Verdict: ❌ ILLEGAL CBA TRANSACTION
```text
CBA Rule Violation:
1. Second Apron aggregation violation: Franchises above the Second Apron
   cannot aggregate multiple outgoing salaries to acquire a player making
   more than their highest single outgoing salary ($15,936,452).
```

### The Strategic Takeaway
Even though Cleveland is sending out more total money ($\$30.0\text{M} > \$28.1\text{M}$), they **cannot legally make the trade** because the Second Apron bans aggregating multiple contracts to acquire a player whose salary exceeds any individual outgoing piece. To acquire White, Cleveland must make a 1-for-1 trade or drop below **$\$207,824,000$** first.

---

## Case Study 4: The San Antonio Spurs Cap Space Arbitrage

### The Scenario
San Antonio sits in **Bracket 0 ($< \text{Tax}, \lambda = 0.00$)** with a committed payroll of **$\$182,366,805$**:
- **San Antonio Outgoing:** Harrison Barnes ($\$19,000,000$) + Kelly Olynyk ($\$13,445,122$) = **$\$32,445,122$**
- **Boston Outgoing:** Derrick White ($\$28,100,000$)

### Valuation & Surplus Delta ($\Delta NSV$)
```text
STATUS: [LEGAL CBA TRANSACTION]

--- SAS SUMMARY ---
Outgoing: Harrison Barnes, Kelly Olynyk ($32,445,122)
Incoming: Derrick White ($28,100,000)
Payroll Shift: $182,366,805 -> $178,021,683 (Bracket 0 -> Bracket 0)
Friction Drag Relief: $+0
Net Surplus Swing (Delta NSV): +$36,822,627

--- BOS SUMMARY ---
Outgoing: Derrick White ($28,100,000)
Incoming: Harrison Barnes, Kelly Olynyk ($32,445,122)
Payroll Shift: $188,993,578 -> $193,338,700 (Bracket 1 -> Bracket 1)
Friction Drag Relief: +$240,391
Net Surplus Swing (Delta NSV): -$36,582,236
```

### The Strategic Takeaway
San Antonio captures **$+$\$36.8M in Net Surplus** because Derrick White ($9.45$ WAR) is an elite positive-surplus asset, and San Antonio's sub-tax status incurs zero apron friction. Boston, sitting in Bracket 1 (Luxury Tax), accepts negative surplus to absorb multiple depth pieces while managing tax brackets.
