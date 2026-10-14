from fastapi import FastAPI
from pydantic import BaseModel, Field
import uuid

app = FastAPI(title="TicketSphere Payment Simulator", version="1.0.0")

class PaymentRequest(BaseModel):
    booking_id: str
    amount: float = Field(gt=0)
    mode: str = "success"

@app.get("/health")
def health():
    return {"service": "payments", "status": "healthy"}

@app.post("/payments")
def pay(payload: PaymentRequest):
    # Deliberately simulated: never processes real card or banking information.
    if payload.mode.lower() == "fail":
        return {"booking_id": payload.booking_id, "status": "failed", "reason": "Simulated payment decline"}
    return {"booking_id": payload.booking_id, "status": "paid", "transaction_id": f"txn-{uuid.uuid4().hex[:10]}", "amount": payload.amount}
