from fastapi.testclient import TestClient

from boston_housing.contracts import FEATURES
from boston_housing.web import create_app


def payload():
    return {key: value["default"] for key, value in FEATURES.items()}


def test_stateless_prediction_health_and_security_headers():
    with TestClient(create_app()) as client:
        health = client.get("/api/health")
        assert health.status_code == 200 and health.json()["scope"] == "historical-research"
        result = client.post("/api/predict", json=payload())
        assert result.status_code == 200
        assert result.headers["x-frame-options"] == "DENY"
        assert result.headers["x-content-type-options"] == "nosniff"
        assert result.json()["model_sha256"] == health.json()["model_sha256"]
        assert client.get("/api/report").json()["feature_names"] == list(payload())


def test_adversarial_api_inputs_and_large_body():
    with TestClient(create_app()) as client:
        for values in [
            {**payload(), "B": 10},
            {**payload(), "RM": "<script>alert(1)</script>"},
            {},
            {**payload(), "LSTAT": 10},
            {**payload(), "RM": True},
        ]:
            assert client.post("/api/predict", json=values).status_code == 422
        assert client.post("/api/predict", content=b"x" * 4097).status_code == 413
        assert (
            client.post("/api/predict", content=b"{}", headers={"content-length": "invalid"}).status_code
            == 413
        )
        assert client.get("/.env").status_code == 404
        assert client.get("/housepred.pkl").status_code == 404
