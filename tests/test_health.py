"Test cases for health functionality."

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    "Test class for healthendpoints functionality."

    @pytest.mark.unit
    def test_basic_ping_endpoint(self, client: TestClient):
        "Test basic ping endpoint functionality."
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    @pytest.mark.unit
    def test_root_endpoint(self, client: TestClient):
        "Test root endpoint functionality."
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert data["status"] == "operational"
        assert "timestamp" in data

    @pytest.mark.unit
    def test_basic_health_check(self, client: TestClient):
        "Test basic health check functionality."
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
        assert "version" in data

    @pytest.mark.integration
    def test_detailed_health_check(self, client: TestClient):
        "Test detailed health check functionality."
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "system" in data["components"]
        for component_name, component_data in data["components"].items():
            assert "status" in component_data

    @pytest.mark.integration
    def test_readiness_check(self, client: TestClient):
        "Test readiness check functionality."
        response = client.get("/api/v1/health/readiness")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert "timestamp" in data

    @pytest.mark.integration
    def test_liveness_check(self, client: TestClient):
        "Test liveness check functionality."
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "alive" in data
        assert "timestamp" in data


class TestHealthMonitoring:
    "Test class for healthmonitoring functionality."

    @pytest.mark.unit
    def test_health_check_response_format(self, client: TestClient):
        "Test health check response format functionality."
        endpoints = ["/ping", "/api/v1/health/", "/api/v1/health/liveness"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "timestamp" in data

    @pytest.mark.integration
    def test_performance_metrics_endpoint(self, client: TestClient):
        "Test performance metrics endpoint functionality."
        response = client.get("/api/v1/health/performance")
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert ("metrics" in data) or ("performance" in data)
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            pass
        else:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
            ]
