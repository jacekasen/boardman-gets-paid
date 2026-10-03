"""Statutory 2023 Collective Bargaining Agreement (CBA) trade matching and apron restriction rules."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from boardman.config import (
    BAND_1_THRESHOLD_2025_26,
    BAND_2_THRESHOLD_2025_26,
    FIRST_APRON_2025_26,
    LUXURY_TAX_2025_26,
    SALARY_CAP_2025_26,
    SECOND_APRON_2025_26,
    TRADE_BUFFER_ALLOWANCE_2025_26,
    get_team_bracket,
)


class TradeComplianceCheck(BaseModel):
    """Detailed compliance breakdown for a single franchise in a proposed trade."""

    team: str
    pre_payroll: float
    post_payroll: float
    pre_bracket: int
    post_bracket: int
    salary_out: float
    salary_in: float
    max_allowable_incoming: float
    is_salary_matching_valid: bool
    is_aggregation_valid: bool
    is_cash_valid: bool
    is_hard_cap_respected: bool
    is_compliant: bool
    violations: list[str] = Field(default_factory=list)


def calculate_max_incoming_salary(
    salary_out: float,
    current_payroll: float,
    salary_cap: float = SALARY_CAP_2025_26,
    first_apron: float = FIRST_APRON_2025_26,
) -> float:
    """Calculate maximum allowable incoming salary under 2023 CBA rules.

    Rules:
    - If current payroll >= First Apron: 100% hard match (salary_in <= salary_out).
    - If non-taxpayer:
      * salary_out <= $7.5M  -> 200% * salary_out + $250k
      * $7.5M < salary_out <= $29.0M -> salary_out + $7.5M
      * salary_out > $29.0M  -> 125% * salary_out + $250k
      (Subject to not crossing the First Apron unless matching permits).
    """
    if salary_out <= 0:
        return 0.0

    # Teams starting above the First Apron are strictly limited to 100%
    if current_payroll >= first_apron:
        return salary_out

    # 2023 CBA Article VII, Section 6(j) Non-taxpayer matching bands (indexed to 2025-26 cap growth)
    if salary_out <= BAND_1_THRESHOLD_2025_26:
        raw_max = (2.00 * salary_out) + TRADE_BUFFER_ALLOWANCE_2025_26
    elif salary_out <= BAND_2_THRESHOLD_2025_26:
        raw_max = salary_out + BAND_1_THRESHOLD_2025_26
    else:
        raw_max = (1.25 * salary_out) + TRADE_BUFFER_ALLOWANCE_2025_26

    # Hard-cap clamp: If taking back raw_max would push total team payroll over the First Apron,
    # the maximum incoming salary is capped at the First Apron line
    post_payroll_candidate = (current_payroll - salary_out) + raw_max
    if post_payroll_candidate > first_apron:
        # Non-taxpayer cannot use non-taxpayer bands to jump past First Apron
        allowable_slack = max(0.0, first_apron - (current_payroll - salary_out))
        # They can always at least match 100% of outgoing salary
        return max(salary_out, allowable_slack)

    return raw_max


def check_trade_compliance(
    team_code: str,
    pre_payroll: float,
    outgoing_contracts: list[float],
    incoming_contracts: list[float],
    outgoing_cash: float = 0.0,
    salary_cap: float = SALARY_CAP_2025_26,
    first_apron: float = FIRST_APRON_2025_26,
    second_apron: float = SECOND_APRON_2025_26,
) -> TradeComplianceCheck:
    """Validate all statutory 2023 CBA trade rules for a single team in a transaction.

    Checks:
    1. Salary matching bounds.
    2. Second Apron salary aggregation prohibition.
    3. Second Apron cash prohibition.
    4. First Apron hard-cap ceiling enforcement.
    """
    salary_out = sum(outgoing_contracts)
    salary_in = sum(incoming_contracts)
    post_payroll = pre_payroll - salary_out + salary_in

    pre_bracket, _ = get_team_bracket(pre_payroll)
    post_bracket, _ = get_team_bracket(post_payroll)

    violations: list[str] = []

    # 1. Salary Matching Check
    max_incoming = calculate_max_incoming_salary(
        salary_out=salary_out,
        current_payroll=pre_payroll,
        salary_cap=salary_cap,
        first_apron=first_apron,
    )
    is_matching_valid = salary_in <= (max_incoming + 1.0)  # +$1 epsilon for float rounding
    if not is_matching_valid:
        violations.append(
            f"Salary matching violation: Incoming salary (${salary_in:,.0f}) exceeds maximum allowable (${max_incoming:,.0f}) based on outgoing (${salary_out:,.0f})."
        )

    # 2. Second Apron Zero Salary Aggregation Rule
    # If a team is above the Second Apron (pre or post trade), they cannot aggregate multiple outgoing
    # players to acquire a single incoming player whose salary exceeds any single outgoing player
    is_aggregation_valid = True
    if pre_payroll >= second_apron or post_payroll >= second_apron:
        if len(outgoing_contracts) > 1 and len(incoming_contracts) > 0:
            max_single_outgoing = max(outgoing_contracts) if outgoing_contracts else 0.0
            # Check if any incoming contract exceeds the largest individual outgoing contract
            aggregated_incoming = [inc for inc in incoming_contracts if inc > max_single_outgoing]
            if aggregated_incoming:
                is_aggregation_valid = False
                violations.append(
                    f"Second Apron aggregation violation: Franchises above the Second Apron cannot aggregate multiple outgoing salaries to acquire a player making more than their highest single outgoing salary (${max_single_outgoing:,.0f})."
                )

    # 3. Second Apron Cash Prohibition
    is_cash_valid = True
    if (pre_payroll >= second_apron or post_payroll >= second_apron) and outgoing_cash > 0:
        is_cash_valid = False
        violations.append(
            f"Second Apron cash violation: Franchises in the Second Apron are forbidden from sending cash in trades (${outgoing_cash:,.0f} attempted)."
        )

    # 4. First Apron Hard-Cap Check
    is_hard_cap_respected = True
    if pre_payroll < first_apron and post_payroll > first_apron:
        # A sub-apron team taking back more salary than sent out that crosses the first apron is restricted
        if salary_in > salary_out:
            is_hard_cap_respected = False
            violations.append(
                f"First Apron hard-cap violation: Trade increases payroll from ${pre_payroll:,.0f} to ${post_payroll:,.0f}, piercing the First Apron (${first_apron:,.0f}) while taking back excess salary."
            )

    is_compliant = is_matching_valid and is_aggregation_valid and is_cash_valid and is_hard_cap_respected

    return TradeComplianceCheck(
        team=team_code,
        pre_payroll=round(pre_payroll, 2),
        post_payroll=round(post_payroll, 2),
        pre_bracket=pre_bracket,
        post_bracket=post_bracket,
        salary_out=round(salary_out, 2),
        salary_in=round(salary_in, 2),
        max_allowable_incoming=round(max_incoming, 2),
        is_salary_matching_valid=is_matching_valid,
        is_aggregation_valid=is_aggregation_valid,
        is_cash_valid=is_cash_valid,
        is_hard_cap_respected=is_hard_cap_respected,
        is_compliant=is_compliant,
        violations=violations,
    )
