# Real-World Case Studies & Empirical Benchmarks

This document reviews the benchmark case studies implemented in [`boardman/case_studies.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/case_studies.py) and featured in the interactive Streamlit application.

---

## Flagship Case Study: The Cleveland–Detroit Apron Escape (The "Thesis-Flip" Trade)

> **Core Research Question:** *What does the `boardman-gets-paid` model conclude that a linear Dollar-per-WAR model gets completely wrong?*

### The Scenario
The Cleveland Cavaliers entered the 2025–26 season as the NBA's lone **Bracket 3 / Second Apron team** with a committed payroll of **$\$211,686,176$**, sitting **$\$3,862,176$** over the Second Apron threshold ($\$207,824,000$). At $\lambda = 0.70$, Cleveland pays **$-\$31,070,854$** in annual friction drag, and their 2033 first-round draft pick is statutorily frozen.

To escape the Second Apron, Cleveland proposes a straight player swap with Detroit:
- **Cleveland Outgoing:** Jarrett Allen ($\$20,000,000$ cap hit, $4.86$ WAR)
- **Detroit Outgoing:** Isaiah Stewart ($\$15,000,000$ cap hit, $1.89$ WAR)

---

### Comparison of Model Verdicts

| Analytical Dimension | Linear $/WAR Model | `boardman-gets-paid` (Apron Friction Engine) |
| :--- | :--- | :--- |
| **Salary Saved** | $+\$5,000,000$ | $+\$5,000,000$ |
| **WAR Contribution Delta** | $-2.97$ WAR ($1.89 - 4.86$) | $-2.97$ WAR ($1.89 - 4.86$) |
| **On-Court Production Delta** | $-\$15,532,720$ | $-\$15,532,720$ |
| **Roster-Wide Friction Relief** | **$\$0$ (Ignored)** | **$+\$15,932,842$ (Apron Escape!)** |
| **2033 Draft Pick Status** | Ignored | **Unfrozen** |
| **Final Franchise Surplus Swing ($\Delta NSV$)** | **$-\$10,532,720$** | **$+\$5,400,122$** |
| **Front Office Verdict** | ❌ **REJECT (Cleveland gets fleeced)** | ✅ **ACCEPT (Cleveland captures +$5.4M net surplus)** |

### Why the Apron Model is Right
A naive linear model assumes franchise payroll state does not matter; it only evaluates the $-2.97$ on-court win drop against the $\$5.0\text{M}$ salary savings. 

In reality, shedding that $\$5.0\text{M}$ reduces Cleveland's payroll to **$\$206,686,176$**, dropping them **below the Second Apron ($<\$207,824,000$) into Bracket 2**.
- Roster friction $\lambda$ drops from $0.70 \to 0.35$ across the entire roster.
- Total roster friction falls from **$\$31.07\text{M} \to \$15.14\text{M}$**, immediately recovering **$+\$15.93\text{M}$ in operational liquidity**.
- This friction relief ($+\$15.93\text{M}$) completely offsets the talent loss ($-\$10.53\text{M}$), resulting in a net franchise value gain of **$+\$5.40\text{M}$**.

---

## Case Study 2: The Kawhi Leonard & LA Clippers Cap Circumvention Ruling (Sept 2026)

### Background & Investigative Timeline
In late 2025, investigative journalist Pablo Torre on *Pablo Torre Finds Out* broke reporting detailing off-the-books financial arrangements between the Los Angeles Clippers, superstar forward Kawhi Leonard, and his business representative Dennis Robertson ("Uncle Dennis").

Following a yearlong independent investigation led by law firm Wachtell, Lipton, Rosen & Katz, the NBA concluded in **September 2026** that the Clippers had engaged in systematic salary-cap circumvention.

### The Scheme
- **The "No-Show" Endorsement Funnel:** The Clippers facilitated tens of millions of dollars in off-court income through team corporate sponsors. Most prominently, climate-fintech firm **Aspiration** signed Leonard to a **$28 million, 4-year contract** ($7.0M/yr) for zero verifiable deliverables.
- **Additional Sponsor Contracts:** Arrangements were also uncovered with **Boingo Wireless** ($672,000 paid for a single one-hour meet-and-greet), **Daktronics**, and **Lockton Insurance**.
- **Uncle Dennis's Demands:** Dennis Robertson was identified as the central figure demanding and coordinating these off-the-cap benefits as a prerequisite for Leonard signing and remaining in Los Angeles.

### Historic NBA Sanctions
1. **$30 Million Team Fine:** The largest fine levied against any franchise in NBA history.
2. **Forfeiture of 5 First-Round Draft Picks:** Stripped of consecutive first-round picks in **2029, 2030, 2031, 2032, and 2033**.
   - Priced at $\$11.5\text{M}$ average rookie surplus curve value = **$\$57.5\text{M}$ in equity destroyed**.
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
  At $P(\text{audit}) = 0.30$, ownership incurs an expected sanction drag of **$\$26.25\text{M}$**, completely wiping out any surplus created by the contract.

**Primary Statutory & Investigative Sources:**
1. Pablo Torre, *Pablo Torre Finds Out* (Meadowlark Media, Sept 2025 – Sept 2026).
2. Wachtell, Lipton, Rosen & Katz, *Report of Independent Investigation to the NBA Board of Governors* (Sept 2026).
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
