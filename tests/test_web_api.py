"""Frontend bridge checks: preserve engine output and reject invalid selections."""
import pytest

from boardman.web_api import snapshot, trade


def test_snapshot_includes_all_teams_and_finite_values():
    import json
    data = snapshot()
    assert len(data["teams"]) == 30
    assert len(data["players"]) > 400
    assert any(p["is_dead_money"] for p in data["players"])
    json.dumps(data, allow_nan=False)


def test_flagship_trade_uses_projected_baseline():
    result = trade(dict(team_a="CLE", team_b="DAL", send_a=["Max Strus"], send_b=["Caleb Martin"]))
    assert result["is_legal"] is True
    assert result["delta_a"]["delta_nsv"] == pytest.approx(15_288_576.43)
    assert result["delta_a"]["post_bracket"] == 2


@pytest.mark.parametrize("changes", [
    {"team_a": "BAD"},
    {"send_a": ["Max Strus", "Max Strus"]},
    {"send_a": "Max Strus"},
    {"send_a": [], "send_b": []},
    {"team_b": "CLE"},
])
def test_invalid_trade_inputs(changes):
    payload = dict(team_a="CLE", team_b="DAL", send_a=["Max Strus"], send_b=["Caleb Martin"])
    payload.update(changes)
    with pytest.raises(ValueError):
        trade(payload)
