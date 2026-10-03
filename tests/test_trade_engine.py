"""Unit tests for the trade simulator engine."""

import pytest

from boardman.trade_engine import evaluate_trade


def test_legal_two_team_trade():
    """Verify evaluation of a legal trade between San Antonio and Boston."""
    trade = evaluate_trade(
        team_a="SAS",
        send_a=["Harrison Barnes", "Kelly Olynyk"],
        team_b="BOS",
        send_b=["Derrick White"],
    )

    assert trade.is_legal
    assert len(trade.violations) == 0
    assert trade.salary_out_a == trade.salary_in_b
    assert trade.salary_out_b == trade.salary_in_a
    assert trade.delta_a.delta_nsv > 0  # SAS gained net surplus
    assert "LEGAL CBA TRANSACTION" in trade.summary()


def test_illegal_second_apron_trade():
    """Verify illegal trade detection when a Second Apron franchise aggregates contracts."""
    trade = evaluate_trade(
        team_a="CLE",
        send_a=["Max Strus", "Dennis Schröder"],
        team_b="BOS",
        send_b=["Derrick White"],
    )

    assert not trade.is_legal
    assert len(trade.violations) > 0
    assert any("Second Apron aggregation violation" in v for v in trade.violations)
    assert "ILLEGAL CBA TRANSACTION" in trade.summary()


def test_dead_money_trade_rejection():
    """Verify that attempting to trade a dead-money/waived contract is rejected as illegal."""
    # 1. Milwaukee waived and stretched Damian Lillard ($22.5M) -> Dead money on MIL
    trade_mil = evaluate_trade(
        team_a="MIL",
        send_a=["Damian Lillard"],  # Milwaukee dead money stretch contract
        team_b="DET",
        send_b=["Isaiah Stewart"],
    )
    assert not trade_mil.is_legal
    assert any("Dead money contract violation" in v for v in trade_mil.violations)

    # 2. Portland waived and stretched Deandre Ayton ($25.5M) -> Dead money on POR
    trade_por = evaluate_trade(
        team_a="POR",
        send_a=["Deandre Ayton"],  # Portland dead money stretch contract
        team_b="DET",
        send_b=["Isaiah Stewart"],
    )
    assert not trade_por.is_legal
    assert any("Dead money contract violation" in v for v in trade_por.violations)

    # 3. Portland has Damian Lillard on active contract ($14.1M) -> Active roster asset (not dead money)
    trade_active = evaluate_trade(
        team_a="POR",
        send_a=["Damian Lillard"],
        team_b="DET",
        send_b=["Isaiah Stewart"],
    )
    # Lillard on POR must NOT trigger a dead-money violation
    assert not any("Dead money contract violation" in v for v in trade_active.violations)


def test_invalid_player_team_rejection():
    """Verify ValueError when attempting to trade a player from the wrong team."""
    with pytest.raises(ValueError, match="is on team"):
        evaluate_trade(
            team_a="SAS",
            send_a=["Nikola Jokic"],  # Jokic is on DEN
            team_b="BOS",
            send_b=["Derrick White"],
        )


def test_same_team_trade_rejection():
    """Verify ValueError when trying to trade within the same franchise."""
    with pytest.raises(ValueError, match="Cannot trade within the same team"):
        evaluate_trade(
            team_a="BOS",
            send_a=["Jayson Tatum"],
            team_b="BOS",
            send_b=["Jaylen Brown"],
        )
