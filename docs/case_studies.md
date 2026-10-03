# Real-World Case Studies & Empirical Benchmarks

This document reviews the three canonical case studies implemented in [`boardman/case_studies.py`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/case_studies.py) and featured in the interactive Streamlit application.

---

## Case Study 1: The Kawhi Leonard & LA Clippers Cap Circumvention Ruling (Sept 2026)

### Background & Investigative Timeline
In late 2025, investigative journalist Pablo Torre on *Pablo Torre Finds Out* broke reporting detailing off-the-books financial arrangements between the Los Angeles Clippers, superstar forward Kawhi Leonard, and his business representative/uncle, Dennis Robertson ("Uncle Dennis").

Following a yearlong independent investigation led by law firm Wachtell, Lipton, Rosen & Katz, the NBA concluded in **September 2026** that the Clippers had engaged in a systematic pattern of salary-cap circumvention.

### The Scheme
- **The "No-Show" Endorsement Funnel:** The Clippers facilitated tens of millions of dollars in off-court income through team corporate sponsors. Most prominently, climate-fintech firm **Aspiration** (heavily invested in by owner Steve Ballmer) signed Leonard to a **$28 million, 4-year contract** for little to no deliverables.
- **Additional Sponsor Contracts:** Arrangements were also uncovered with **Boingo Wireless** ($672,000 paid for a single one-hour meet-and-greet), **Daktronics**, and **Lockton Insurance**.
- **Uncle Dennis's Role:** Dennis Robertson was identified as the central figure demanding and coordinating these off-the-cap benefits as a prerequisite for Leonard signing and remaining in Los Angeles.

### Historic NBA Sanctions
1. **$30 Million Team Fine:** The largest fine levied against any franchise in NBA history.
2. **Forfeiture of 5 First-Round Draft Picks:** Stripped of consecutive first-round picks in **2029, 2030, 2031, 2032, and 2033**, severely impacting the franchise's draft assets.
3. **Executive Suspensions:**
   - **Steve Ballmer** (Owner): 1-year suspension from all league and team activities.
   - **Gillian Zucker** (President of Business Ops): 1-year suspension.
   - **Lawrence Frank** (President of Basketball Ops): 6-month suspension.
4. **Dennis Robertson Banned:** 5-year league-wide ban from all NBA business.
5. **Kawhi Leonard Restitution:** Fined **$700,000** in restitution; cleared to be traded back to the Toronto Raptors.

### Modeling Shadow Compensation in `boardman`
In [`run_kawhi_circumvention_case_study`](file:///Users/jankasen/dev/boardman-gets-paid/boardman/case_studies.py#L42):
- **On-the-Books Cap Hit:** $\$50,000,000$ (32.3% of cap, producing 14.3 WAR).
- **Official Net Surplus ($NSV$):** **$+$\$24.8M**.
- **Circumvented Real Cost:** Adding the $\$7,000,000$ annual Aspiration subsidy increases effective annual investment to $\$57,000,000$.
- **Circumvented Net Surplus:** **$+$\$17.8M** ($\$7.0\text{M}$ in immediate surplus erosion).

*Insight:* Off-the-cap payments artificially lower on-the-books salary, hiding true economic investment while exposing the franchise to catastrophic draft-capital forfeiture.

---

## Case Study 2: The Cleveland Cavaliers Second Apron Aggregation Trap

### The Scenario
For the 2025–26 season, the Cleveland Cavaliers committed **$\$211,686,176$** in active payroll, making them the league's lone **Bracket 3 / Second Apron franchise ($\lambda = 0.70$)**:

- **Total Roster Friction Drag:** **$-\$31,070,854$** annually.
- **Top Individual Friction Penalties:**
  - Evan Mobley ($\$46.4\text{M}$): $-\$9.74\text{M}$ friction.
  - Donovan Mitchell ($\$46.4\text{M}$): $-\$9.74\text{M}$ friction.
  - James Harden ($\$39.4\text{M}$): $-\$7.04\text{M}$ friction.

### The Illegal Proposed Trade
Cleveland attempts to combine two veteran starters to acquire Boston guard Derrick White:
- **Cleveland Outgoing:** Max Strus ($\$15,936,452$) + Dennis Schröder ($\$14,104,000$) = **$\$30,040,452$**
- **Boston Outgoing:** Derrick White ($\$28,100,000$)

### Statutory Verdict: [ILLEGAL CBA TRANSACTION]
```text
CBA Rule Violation:
1. Second Apron aggregation violation: Franchises above the Second Apron
   cannot aggregate multiple outgoing salaries to acquire a player making
   more than their highest single outgoing salary ($15,936,452).
```

### The Strategic Takeaway
Even though Cleveland is sending out more total money ($\$30.0\text{M} > \$28.1\text{M}$), they **cannot legally make the trade** because the Second Apron bans aggregating multiple contracts to acquire a player whose salary exceeds any individual outgoing piece. To escape, Cleveland must either execute a 1-for-1 swap or shed salary to drop below **$\$207,824,000$**.

---

## Case Study 3: The San Antonio Spurs Cap Space Arbitrage

### The Scenario
San Antonio sits comfortably in **Bracket 0 ($< \text{Tax}, \lambda = 0.00$)** with a committed payroll of **$\$182,366,805$**:

### The Proposed Legal Trade
San Antonio sends two veteran rotation players to Boston for Derrick White:
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
San Antonio captures **$+$\$36.8M in Net Surplus** because Derrick White (9.45 WAR) is an elite positive-surplus asset, and San Antonio's sub-tax status incurs zero apron friction. Boston, sitting in Bracket 1 (Luxury Tax), accepts negative surplus to absorb multiple depth pieces while managing tax brackets.
