"""Unit tests for statutory CBA trade matching rules, bands, and apron prohibitions."""

import pytest

from boardman.cba_rules import (
    calculate_max_incoming_salary,
    check_trade_compliance,
)
from boardman.config import (
    BAND_1_THRESHOLD_2025_26,
    BAND_2_THRESHOLD_2025_26,
    FIRST_APRON_2025_26,
    SECOND_APRON_2025_26,
    TRADE_BUFFER_ALLOWANCE_2025_26,
)


def test_non_taxpayer_matching_bands():
    """Verify statutory matching bands for teams below the First Apron (indexed to 2025-26 cap growth)."""
    sub_tax_payroll = 140_000_000.0

    # Band 1: Outgoing <= $8.53M -> 200% + $284k
    max_in_5m = calculate_max_incoming_salary(5_000_000.0, sub_tax_payroll)
    assert max_in_5m == pytest.approx((2.0 * 5_000_000.0) + TRADE_BUFFER_ALLOWANCE_2025_26)

    # Band 2: $8.53M < Outgoing <= $32.97M -> Outgoing + $8.53M
    max_in_20m = calculate_max_incoming_salary(20_000_000.0, sub_tax_payroll)
    assert max_in_20m == pytest.approx(20_000_000.0 + BAND_1_THRESHOLD_2025_26)

    # Band 3: Outgoing > $32.97M -> 125% + $284k
    max_in_35m = calculate_max_incoming_salary(35_000_000.0, sub_tax_payroll)
    assert max_in_35m == pytest.approx((1.25 * 35_000_000.0) + TRADE_BUFFER_ALLOWANCE_2025_26)


def test_first_apron_hard_match():
    """Teams above the First Apron are strictly limited to 100% of outgoing salary."""
    first_apron_payroll = FIRST_APRON_2025_26 + 1_000_000.0

    max_in = calculate_max_incoming_salary(25_000_000.0, first_apron_payroll)
    assert max_in == pytest.approx(25_000_000.0)


def test_non_taxpayer_hard_cap_clamping():
    """Non-taxpayer taking back salary that would pierce First Apron is clamped."""
    # Team payroll is $193M ($2.945M below First Apron of $195.945M)
    payroll = FIRST_APRON_2025_26 - 2_945_000.0
    out_salary = 10_000_000.0

    # Normal band would allow $10M + $7.5M = $17.5M (which would reach $200.5M, deep into 1st apron)
    max_in = calculate_max_incoming_salary(out_salary, payroll)

    # Must clamp to allowable slack ($10M outgoing + $2.945M slack = $12.945M)
    assert max_in == pytest.approx(out_salary + 2_945_000.0)
    assert (payroll - out_salary + max_in) <= (FIRST_APRON_2025_26 + 1.0)


def test_second_apron_aggregation_prohibition():
    """Second Apron teams cannot aggregate salaries to acquire a player making more than their highest outgoing contract."""
    sec_apron_payroll = SECOND_APRON_2025_26 + 2_000_000.0

    # Outgoing: Two contracts ($15M and $10M = $25M total)
    outgoing = [15_000_000.0, 10_000_000.0]

    # Incoming: One contract of $24M (under total outgoing $25M, but > max single $15M)
    incoming_illegal = [24_000_000.0]

    comp_illegal = check_trade_compliance(
        team_code="TEST",
        pre_payroll=sec_apron_payroll,
        outgoing_contracts=outgoing,
        incoming_contracts=incoming_illegal,
    )
    assert not comp_illegal.is_compliant
    assert not comp_illegal.is_aggregation_valid
    assert any("Second Apron aggregation violation" in v for v in comp_illegal.violations)

    # Incoming: Two contracts of $14M and $9M (both <= max single $15M)
    incoming_legal = [14_000_000.0, 9_000_000.0]
    comp_legal = check_trade_compliance(
        team_code="TEST",
        pre_payroll=sec_apron_payroll,
        outgoing_contracts=outgoing,
        incoming_contracts=incoming_legal,
    )
    assert comp_legal.is_aggregation_valid


def test_second_apron_cash_prohibition():
    """Second Apron teams are forbidden from sending outgoing cash."""
    sec_apron_payroll = SECOND_APRON_2025_26 + 1_000_000.0
    comp = check_trade_compliance(
        team_code="TEST",
        pre_payroll=sec_apron_payroll,
        outgoing_contracts=[20_000_000.0],
        incoming_contracts=[18_000_000.0],
        outgoing_cash=1_000_000.0,
    )
    assert not comp.is_compliant
    assert not comp.is_cash_valid
    assert any("Second Apron cash violation" in v for v in comp.violations)
