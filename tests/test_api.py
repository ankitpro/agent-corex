"""
Tests for the FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_endpoint(self):
        """Verify health endpoint returns status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRetrieveToolsEndpoint:
    """Tests for the /retrieve_tools endpoint."""

    def test_retrieve_tools_basic(self):
        """Verify retrieve_tools returns tools for a valid query."""
        response = client.get("/retrieve_tools?query=edit file")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_retrieve_tools_returns_ranked_results(self):
        """Verify retrieve_tools returns results ranked by relevance."""
        response = client.get("/retrieve_tools?query=edit")
        assert response.status_code == 200
        result = response.json()
        # Should find edit_file as top result
        assert len(result) > 0
        assert result[0]["name"] == "edit_file"

    def test_retrieve_tools_top_k_parameter(self):
        """Verify top_k parameter limits result count."""
        response = client.get("/retrieve_tools?query=file&top_k=1")
        assert response.status_code == 200
        result = response.json()
        assert len(result) <= 1

    def test_retrieve_tools_default_top_k(self):
        """Verify default top_k=5 is applied."""
        response = client.get("/retrieve_tools?query=file")
        assert response.status_code == 200
        result = response.json()
        # Should have at most 5 results by default
        assert len(result) <= 5

    def test_retrieve_tools_irrelevant_query(self):
        """Verify irrelevant queries return empty list."""
        response = client.get("/retrieve_tools?query=kubernetes+cluster")
        assert response.status_code == 200
        result = response.json()
        # No tools should match this query
        assert result == []

    def test_retrieve_tools_missing_query(self):
        """Verify endpoint handles missing query parameter."""
        response = client.get("/retrieve_tools")
        # FastAPI should return 422 for missing required parameter
        assert response.status_code == 422

    def test_retrieve_tools_response_structure(self):
        """Verify response contains tool objects with expected fields."""
        response = client.get("/retrieve_tools?query=test")
        assert response.status_code == 200
        result = response.json()
        if result:
            # Tools should have at least name and description
            tool = result[0]
            assert "name" in tool
            assert isinstance(tool["name"], str)
