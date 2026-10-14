import os
import sqlite3
import uuid
import httpx
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

EVENTS_URL = os.getenv("EVENTS_URL", "http://events:8000")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory:8000")
PAYMENTS_URL = os.getenv("PAYMENTS_URL", "http://payments:8000")
DB_PATH = os.getenv("DB_PATH", "/data/bookings.db")
app = FastAPI(title="TicketSphere Booking Service", version="1.0.0")

@contextmanager
def connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS bookings (id TEXT PRIMARY KEY, event_id TEXT NOT NULL, event_name TEXT NOT NULL, seat_id TEXT NOT NULL, customer_name TEXT NOT NULL, amount REAL NOT NULL, status TEXT NOT NULL, transaction_id TEXT)")

@app.on_event("startup")
def startup():
    init_db()

class BookingRequest(BaseModel):
    event_id: str
    seat_id: str
    customer_name: str = Field(min_length=1, max_length=80)
    payment_mode: str = "success"

@app.get("/health")
def health():
    return {"service": "booking", "status": "healthy"}

@app.get("/bookings")
def list_bookings():
    with connection() as conn:
        rows = conn.execute("SELECT * FROM bookings ORDER BY rowid DESC").fetchall()
    return [dict(row) for row in rows]

@app.post("/bookings")
def create_booking(payload: BookingRequest):
    booking_id = f"bk-{uuid.uuid4().hex[:10]}"
    try:
        with httpx.Client(timeout=4.0) as client:
            event_response = client.get(f"{EVENTS_URL}/events/{payload.event_id}")
            if event_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Event not found")
            event = event_response.json()
            reserve_response = client.post(f"{INVENTORY_URL}/reserve", json={"event_id": payload.event_id, "seat_id": payload.seat_id, "booking_id": booking_id})
            if reserve_response.status_code == 409:
                raise HTTPException(status_code=409, detail="Seat has already been reserved or booked")
            if reserve_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Seat inventory service could not reserve the seat")
            payment_response = client.post(f"{PAYMENTS_URL}/payments", json={"booking_id": booking_id, "amount": event["price"], "mode": payload.payment_mode})
            if payment_response.status_code != 200:
                client.post(f"{INVENTORY_URL}/release", json={"event_id": payload.event_id, "seat_id": payload.seat_id, "booking_id": booking_id})
                raise HTTPException(status_code=502, detail="Payment service unavailable; seat reservation released")
            payment = payment_response.json()
            if payment["status"] != "paid":
                client.post(f"{INVENTORY_URL}/release", json={"event_id": payload.event_id, "seat_id": payload.seat_id, "booking_id": booking_id})
                with connection() as conn:
                    conn.execute("INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (booking_id, payload.event_id, event["name"], payload.seat_id, payload.customer_name, event["price"], "payment_failed", None))
                raise HTTPException(status_code=402, detail="Payment declined. Seat released; please try again.")
            confirm_response = client.post(f"{INVENTORY_URL}/confirm", json={"event_id": payload.event_id, "seat_id": payload.seat_id, "booking_id": booking_id})
            if confirm_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Payment succeeded but seat confirmation failed; contact support")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"A dependent service is unavailable: {exc.__class__.__name__}")
    record = {"id": booking_id, "event_id": payload.event_id, "event_name": event["name"], "seat_id": payload.seat_id, "customer_name": payload.customer_name, "amount": event["price"], "status": "confirmed", "transaction_id": payment.get("transaction_id")}
    with connection() as conn:
        conn.execute("INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(record.values()))
    return record
