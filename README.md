# TicketSphere — Cloud-Native Event Booking Microservices

TicketSphere is a college DevOps lab project demonstrating a small event-booking platform built from independently containerized services. It runs locally with Docker Compose; no cloud account or real payment provider is required.

## Features

- API-driven event catalogue with 10 sample Hyderabad experiences, categories, search, event detail pages and live seat selection.
- Seat inventory stored in SQLite with persistent Docker volumes.
- Atomic seat reservation: a conditional database update ensures only one request can reserve a seat.
- Booking workflow orchestrates event lookup, seat reservation, simulated payment, and seat confirmation.
- Simulated payment success/failure. A declined payment releases the reserved seat.
- API Gateway gives the browser one public entry point.
- Service health endpoints, Docker health checks, restart policies, automated tests, and a BookMyShow-inspired responsive experience with event discovery, category filters, event details, seat selection, checkout modal, booking history, and live service health. The frontend fetches data from the backend APIs; booking and seat states are persisted by the services.
- Payment simulation only: do not enter real card or banking details.

## Architecture

```text
Browser
   |
   v
API Gateway (port 8080)
   |------> Event Service
   |------> Seat Inventory Service ----> inventory_data volume
   |------> Booking Service -----------> booking_data volume
                    |       |
                    v       v
              Inventory   Payment Simulator
```

The backend services are not published directly to the host. They communicate using Docker Compose service names on the private Compose network. Only the gateway is published on host port 8080.

## Prerequisites

- Docker Desktop installed and running on Windows.
- Docker Compose v2 (`docker compose` command).

## Run the application

Open PowerShell in the extracted `ticketsphere` folder and run:

```powershell
docker compose up --build -d
docker compose ps
```

Open **http://localhost:8080** in your browser. API documentation is available at **http://localhost:8080/docs**. To inspect service logs:

```powershell
docker compose logs -f
```

Stop the services while retaining the database volumes:

```powershell
docker compose down
```

To remove the application and its stored demo bookings/seats too:

```powershell
docker compose down -v
```

## Try the demo

1. Search for an event or filter by category. Open an event to see its details.
2. Choose seats from the live seat map (up to six per checkout).
3. Complete the simulated checkout, then open **My bookings** to view the booking references.
4. Refresh the page: confirmed seat availability and booking history are loaded from the backend services and persist in Docker volumes.
5. Try a declined payment; the reservation should be released.



1. Open the dashboard and check that all four backend services are healthy.
2. Select an event, select an available seat, enter a name, and keep **Successful payment** selected.
3. Confirm the booking and show the booking reference and recent bookings.
4. Try the same seat again; the service should reject it with a conflict.
5. Choose another available seat and select **Simulate payment failure**. The booking should fail and the seat should become available again.
6. Stop a service to demonstrate fault detection:

   ```powershell
   docker compose stop payments
   ```

   Refresh the dashboard and observe the health status. Restart it afterward:

   ```powershell
   docker compose start payments
   ```

   Note: the booking workflow cannot complete new bookings while the payment service is down. The gateway dashboard can still display the other services.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/events` | List events |
| GET | `/api/events/{event_id}/seats` | List seats and status |
| POST | `/api/bookings` | Create a booking |
| GET | `/api/bookings` | List booking records |
| GET | `/api/services` | Check backend health |
| GET | `/health` | Gateway health check |

Example booking body:

```json
{
  "event_id": "evt-101",
  "seat_id": "A01",
  "customer_name": "Demo User",
  "payment_mode": "success"
}
```

Use `"payment_mode": "fail"` to simulate a declined payment. No actual money is moved.

## Run tests locally (optional)

Use Python 3.12 or compatible, from the project root:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
pytest -q
```

The tests cover event lookup, reservation conflict handling, seat confirmation, and seat release. Docker builds each service separately from the shared `Dockerfile.service` by setting the `SERVICE_DIR` build argument.

## Services and responsibilities

- **Gateway:** public HTTP entry point and routing for the frontend.
- **Event Service:** returns event metadata and prices.
- **Seat Inventory Service:** owns seat states and applies atomic reservation updates.
- **Booking Service:** coordinates the booking workflow and persists booking records.
- **Payment Simulator:** returns simulated payment success/failure.

## Important scope notes

- This is an educational local deployment, not a production ticketing/payment system.
- Payment is simulated and the workflow is intentionally simplified; it is not a full distributed transaction or production-grade saga implementation.
- SQLite is used to keep setup light. For a production-scale implementation, consider PostgreSQL, stronger idempotency and compensation handling, authentication, rate limiting, and a message broker.
- Docker Compose is used for local multi-container deployment. Kubernetes and public-cloud deployment are not required for this version.
