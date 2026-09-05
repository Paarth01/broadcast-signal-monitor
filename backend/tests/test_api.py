import time

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


def test_list_streams_includes_media_and_ptp_devices():
    with TestClient(app) as client:
        time.sleep(0.5)
        res = client.get("/api/streams")
        assert res.status_code == 200
        data = res.json()

        names = {s["name"] for s in data}
        assert "camera-1-studio-a" in names
        assert "ptp-grandmaster" in names

        kinds = {s["kind"] for s in data}
        assert kinds == {"media", "ptp_device"}


def test_get_known_stream_returns_live_metrics():
    with TestClient(app) as client:
        time.sleep(0.5)
        res = client.get("/api/streams/camera-1-studio-a")
        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "camera-1-studio-a"
        assert "bitrate_mbps" in body["metrics"]
        assert body["priority"] is None  # no fault injected, should be healthy


def test_get_unknown_stream_returns_404():
    with TestClient(app) as client:
        res = client.get("/api/streams/does-not-exist")
        assert res.status_code == 404


def test_inject_fault_on_unknown_stream_returns_404():
    with TestClient(app) as client:
        res = client.post(
            "/api/simulate/fault",
            json={"stream_name": "does-not-exist", "fault_type": "dropout"},
        )
        assert res.status_code == 404


def test_fault_injection_flows_through_to_priority_and_fault_log():
    with TestClient(app) as client:
        res = client.post(
            "/api/simulate/fault",
            json={"stream_name": "ob-van-uplink", "fault_type": "dropout", "duration_seconds": 3},
        )
        assert res.status_code == 200

        time.sleep(0.6)  # let a few sped-up ticks land

        detail = client.get("/api/streams/ob-van-uplink").json()
        assert detail["priority"] == 1

        faults = client.get("/api/faults").json()
        assert any(f["stream_name"] == "ob-van-uplink" and f["priority"] == 1 for f in faults)


def test_ptp_rogue_master_fault_is_priority_1():
    with TestClient(app) as client:
        res = client.post(
            "/api/simulate/fault",
            json={"stream_name": "ptp-slave-ob-van", "fault_type": "ptp_rogue_master", "duration_seconds": 3},
        )
        assert res.status_code == 200

        time.sleep(0.6)

        detail = client.get("/api/streams/ptp-slave-ob-van").json()
        assert detail["priority"] == 1
        assert "rogue" in detail["reason"].lower()


def test_fault_is_marked_resolved_after_stream_recovers():
    with TestClient(app) as client:
        res = client.post(
            "/api/simulate/fault",
            json={"stream_name": "camera-1-studio-a", "fault_type": "dropout", "duration_seconds": 1},
        )
        assert res.status_code == 200

        time.sleep(0.6)
        faults = client.get("/api/faults").json()
        active = next(f for f in faults if f["stream_name"] == "camera-1-studio-a")
        assert active["resolved"] is False

        time.sleep(1.5)  # let the 1s fault window expire and the stream recover
        faults = client.get("/api/faults").json()
        recovered = next(f for f in faults if f["stream_name"] == "camera-1-studio-a")
        assert recovered["resolved"] is True


def test_stream_history_returns_persisted_points_oldest_first():
    with TestClient(app) as client:
        time.sleep(1.0)  # let several ticks land in the DB
        history = client.get("/api/streams/camera-1-studio-a/history").json()
        assert len(history) >= 2
        assert "jitter_ms" in history[0]["metrics"]
        # oldest first: timestamps should be non-decreasing
        timestamps = [h["timestamp"] for h in history]
        assert timestamps == sorted(timestamps)


def test_stream_history_for_unknown_stream_returns_404():
    with TestClient(app) as client:
        res = client.get("/api/streams/does-not-exist/history")
        assert res.status_code == 404
