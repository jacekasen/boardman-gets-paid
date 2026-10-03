"""Frontend bridge checks: snapshot data integrity and serialization."""

import json
from boardman.web_api import snapshot


def test_snapshot_includes_all_teams_and_finite_values():
    data = snapshot()
    assert len(data["teams"]) == 30
    assert len(data["players"]) > 400
    assert any(p["is_dead_money"] for p in data["players"])
    serialized = json.dumps(data, allow_nan=False)
    assert len(serialized) > 10_000


def test_snapshot_metrics():
    data = snapshot()
    assert data["season"] == "2025-26"
    assert data["costPerWin"] > 4_000_000
    assert "thresholds" in data
    assert data["thresholds"]["cap"] == 154_647_000
