import os
import sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "/data/inventory.db")
app = FastAPI(title="TicketSphere Seat Inventory Service", version="1.0.0")

@contextmanager
def connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS seats (event_id TEXT NOT NULL, seat_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'available', booking_id TEXT, PRIMARY KEY(event_id, seat_id))")
        for event_id, count in [("evt-101", 30), ("evt-102", 24), ("evt-103", 20), ("evt-104", 30), ("evt-105", 24), ("evt-106", 20), ("evt-107", 30), ("evt-108", 24), ("evt-109", 20), ("evt-110", 30)]:
            for number in range(1, count + 1):
                conn.execute("INSERT OR IGNORE INTO seats(event_id, seat_id) VALUES (?, ?)", (event_id, f"A{number:02d}"))

@app.on_event("startup")
def startup():
    init_db()

class Reservation(BaseModel):
    event_id: str
    seat_id: str
    booking_id: str = Field(min_length=1)

class Release(BaseModel):
    event_id: str
    seat_id: str
    booking_id: str

@app.get("/health")
def health():
    return {"service": "inventory", "status": "healthy"}

@app.get("/events/{event_id}/seats")
def list_seats(event_id: str):
    with connection() as conn:
        rows = conn.execute("SELECT seat_id, status FROM seats WHERE event_id=? ORDER BY seat_id", (event_id,)).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No seats found for event")
    return [{"seat_id": row["seat_id"], "status": row["status"]} for row in rows]

@app.post("/reserve")
def reserve(payload: Reservation):
    # A single conditional UPDATE makes reservation atomic: only one concurrent request can win.
    with connection() as conn:
        cursor = conn.execute("UPDATE seats SET status='reserved', booking_id=? WHERE event_id=? AND seat_id=? AND status='available'", (payload.booking_id, payload.event_id, payload.seat_id))
        if cursor.rowcount != 1:
            exists = conn.execute("SELECT 1 FROM seats WHERE event_id=? AND seat_id=?", (payload.event_id, payload.seat_id)).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="Seat not found")
            raise HTTPException(status_code=409, detail="Seat is no longer available")
    return {"event_id": payload.event_id, "seat_id": payload.seat_id, "booking_id": payload.booking_id, "status": "reserved"}

@app.post("/release")
def release(payload: Release):
    with connection() as conn:
        cursor = conn.execute("UPDATE seats SET status='available', booking_id=NULL WHERE event_id=? AND seat_id=? AND booking_id=? AND status='reserved'", (payload.event_id, payload.seat_id, payload.booking_id))
    return {"released": cursor.rowcount == 1}

@app.post("/confirm")
def confirm(payload: Release):
    with connection() as conn:
        cursor = conn.execute("UPDATE seats SET status='booked' WHERE event_id=? AND seat_id=? AND booking_id=? AND status='reserved'", (payload.event_id, payload.seat_id, payload.booking_id))
    if cursor.rowcount != 1:
        raise HTTPException(status_code=409, detail="Reservation could not be confirmed")
    return {"event_id": payload.event_id, "seat_id": payload.seat_id, "status": "booked"}
