from __future__ import annotations

import pytest

from cgalpha_v3.gui import server


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_state():
    # Reset relevante de estado global entre tests
    server._system_state.update(
        {
            "max_drawdown_session_pct": 5.0,
            "max_position_size_pct": 2.0,
            "max_signals_per_hour": 10,
            "min_signal_quality_score": 0.65,
            "primary_source_gap": False,
            "experiment_loop_status": "idle",
        }
    )


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {server.AUTH_TOKEN}"}


def test_risk_params_requires_auth(client):
    resp = client.get("/api/risk/params")
    assert resp.status_code == 401


def test_get_risk_params_has_all_fields(client):
    resp = client.get("/api/risk/params", headers=_auth_headers())
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["max_drawdown_session_pct"] == 5.0
    assert body["max_position_size_pct"] == 2.0
    assert body["max_signals_per_hour"] == 10
    assert body["min_signal_quality_score"] == 0.65


def test_post_risk_params_updates_all_fields(client):
    payload = {
        "max_drawdown_session_pct": 4.5,
        "max_position_size_pct": 1.5,
        "max_signals_per_hour": 7,
        "min_signal_quality_score": 0.72,
    }
    resp = client.post("/api/risk/params", json=payload, headers=_auth_headers())
    assert resp.status_code == 200
    body = resp.get_json()

    assert set(body["updated"]) == set(payload.keys())
    assert body["all"]["max_drawdown_session_pct"] == 4.5
    assert body["all"]["max_position_size_pct"] == 1.5
    assert body["all"]["max_signals_per_hour"] == 7
    assert body["all"]["min_signal_quality_score"] == 0.72

    check = client.get("/api/risk/params", headers=_auth_headers()).get_json()
    assert check["max_drawdown_session_pct"] == 4.5
    assert check["max_position_size_pct"] == 1.5
    assert check["max_signals_per_hour"] == 7
    assert check["min_signal_quality_score"] == 0.72


@pytest.mark.parametrize(
    "payload",
    [
        {"max_signals_per_hour": 0},
        {"min_signal_quality_score": -0.01},
        {"min_signal_quality_score": 1.01},
        {"max_drawdown_session_pct": -1.0},
        {"max_position_size_pct": -0.1},
    ],
)
def test_post_risk_params_rejects_invalid_ranges(client, payload):
    resp = client.post("/api/risk/params", json=payload, headers=_auth_headers())
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body
