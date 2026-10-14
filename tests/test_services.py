"""Focused API tests for the Event and Seat Inventory services."""
import importlib

from fastapi.testclient import TestClient


def test_event_catalog():
    events_module = importlib.import_module("events.main")
    with TestClient(events_module.app) as client:
        response = client.get("/events")
        assert response.status_code == 200
        assert len(response.json()) >= 3
        assert client.get("/events/evt-101").json()["name"] == "Hyderabad Tech Summit"
        assert client.get("/events/does-not-exist").status_code == 404


def test_seat_can_only_be_reserved_once(tmp_path, monkeypatch):
    inventory = importlib.import_module("inventory.main")
    monkeypatch.setattr(inventory, "DB_PATH", str(tmp_path / "inventory.db"))
    inventory.init_db()
    with TestClient(inventory.app) as client:
        payload = {"event_id": "evt-101", "seat_id": "A01", "booking_id": "bk-test-1"}
        first = client.post("/reserve", json=payload)
        assert first.status_code == 200
        second = client.post("/reserve", json={**payload, "booking_id": "bk-test-2"})
        assert second.status_code == 409
        assert client.post("/confirm", json=payload).status_code == 200
        seats = client.get("/events/evt-101/seats").json()
        assert next(seat for seat in seats if seat["seat_id"] == "A01")["status"] == "booked"


def test_failed_reservation_can_be_released(tmp_path, monkeypatch):
    inventory = importlib.import_module("inventory.main")
    monkeypatch.setattr(inventory, "DB_PATH", str(tmp_path / "inventory-release.db"))
    inventory.init_db()
    with TestClient(inventory.app) as client:
        payload = {"event_id": "evt-102", "seat_id": "A02", "booking_id": "bk-release"}
        assert client.post("/reserve", json=payload).status_code == 200
        assert client.post("/release", json=payload).json()["released"] is True
        seats = client.get("/events/evt-102/seats").json()
        assert next(seat for seat in seats if seat["seat_id"] == "A02")["status"] == "available"
