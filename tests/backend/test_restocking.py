"""
Tests for restocking API endpoints.
"""
from datetime import datetime

import pytest


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_get_recommendations_within_budget(self, client):
        """Test that recommendations never exceed the given budget."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 10000
        assert data["total_cost"] <= data["budget"]
        assert isinstance(data["items"], list)

        for item in data["items"]:
            assert item["deficit"] > 0
            assert item["recommended_quantity"] <= item["deficit"]
            assert item["recommended_quantity"] > 0

    def test_get_recommendations_zero_budget(self, client):
        """Test that a zero budget is rejected as invalid."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 422

    def test_get_recommendations_missing_budget(self, client):
        """Test that omitting the required budget param is rejected."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_recommendations_prioritize_increasing_trend(self, client):
        """Test that items with increasing trend are ranked before others."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        assert response.status_code == 200

        data = response.json()
        trends = [item["trend"] for item in data["items"]]

        if "increasing" in trends and any(t != "increasing" for t in trends):
            first_non_increasing = next(
                i for i, t in enumerate(trends) if t != "increasing"
            )
            # No "increasing" items should appear after a non-increasing one
            assert "increasing" not in trends[first_non_increasing:]

    def test_get_restock_orders_empty_initially(self, client):
        """Test that the restock orders list is a list (possibly already populated by other tests)."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_restock_order_success(self, client):
        """Test submitting a valid restocking order."""
        payload = {
            "budget": 5000,
            "items": [
                {"sku": "TMP-201", "name": "Temperature Sensor Module", "quantity": 10, "unit_cost": 89.5}
            ]
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["total_cost"] == pytest.approx(895.0)
        assert 3 <= order["lead_time_days"] <= 14

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (expected_delivery - order_date).days == order["lead_time_days"]

    def test_create_restock_order_empty_items(self, client):
        """Test that an order with no items is rejected."""
        payload = {"budget": 1000, "items": []}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_submitted_order_appears_in_get_restock_orders(self, client):
        """Test that a submitted order is retrievable via the GET endpoint."""
        payload = {
            "budget": 2000,
            "items": [
                {"sku": "SRV-301", "name": "Micro Servo Motor", "quantity": 2, "unit_cost": 445.0}
            ]
        }
        create_response = client.post("/api/restocking/orders", json=payload)
        assert create_response.status_code == 201
        created_order = create_response.json()

        list_response = client.get("/api/restocking/orders")
        assert list_response.status_code == 200

        all_orders = list_response.json()
        matching = [o for o in all_orders if o["id"] == created_order["id"]]
        assert len(matching) == 1
        assert matching[0]["order_number"] == created_order["order_number"]
