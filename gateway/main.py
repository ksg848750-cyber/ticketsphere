import os
import httpx
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

EVENTS_URL = os.getenv("EVENTS_URL", "http://events:8000")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory:8000")
BOOKING_URL = os.getenv("BOOKING_URL", "http://booking:8000")
BASE_DIR = Path(__file__).parent
app = FastAPI(title="TicketSphere API Gateway", version="1.0.0")

@app.get("/health")
def health():
    return {"service": "gateway", "status": "healthy"}

async def forward(method: str, url: str, **kwargs):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(method, url, **kwargs)
        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text}
        return JSONResponse(status_code=response.status_code, content=body)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="A backend service is currently unavailable")

@app.get("/api/events")
async def events(category: str | None = None, q: str | None = None):
    params = {key: value for key, value in {"category": category, "q": q}.items() if value}
    return await forward("GET", f"{EVENTS_URL}/events", params=params)

@app.get("/api/events/{event_id}")
async def event_detail(event_id: str):
    return await forward("GET", f"{EVENTS_URL}/events/{event_id}")

@app.get("/api/events/{event_id}/seats")
async def seats(event_id: str):
    return await forward("GET", f"{INVENTORY_URL}/events/{event_id}/seats")

@app.post("/api/bookings")
async def create_booking(request: Request):
    payload = await request.json()
    return await forward("POST", f"{BOOKING_URL}/bookings", json=payload)

@app.get("/api/bookings")
async def bookings():
    return await forward("GET", f"{BOOKING_URL}/bookings")

@app.get("/api/services")
async def service_health():
    services = {"events": EVENTS_URL, "inventory": INVENTORY_URL, "booking": BOOKING_URL, "payments": os.getenv("PAYMENTS_URL", "http://payments:8000")}
    results = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, base_url in services.items():
            try:
                response = await client.get(f"{base_url}/health")
                results[name] = "healthy" if response.status_code == 200 else "unhealthy"
            except httpx.RequestError:
                results[name] = "unavailable"
    return results

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE_DIR / "index.html").read_text(encoding="utf-8")
