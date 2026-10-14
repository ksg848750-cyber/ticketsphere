# TicketSphere — Project Explanation Notes

## Problem statement
Build and test a cloud-native application using microservices architecture. TicketSphere demonstrates event browsing and seat booking through independently containerized services.

## Why microservices?
The system separates event information, seat inventory, booking coordination, and payment simulation into services with distinct responsibilities. Services expose HTTP APIs and can be built and restarted independently. The API Gateway is the only service exposed to the host.

## Why cloud-native?
The project uses container images, environment-based configuration, service-name networking, health checks, restart policies, persistent volumes, and automated tests. It runs locally using Docker Compose; cloud-native design does not require that this lab version be deployed to a public cloud.

## Main booking flow
1. The browser requests events through the gateway.
2. The gateway forwards the request to the Event Service or Inventory Service.
3. When a booking is submitted, the gateway forwards it to the Booking Service.
4. The Booking Service validates the event, requests an atomic seat reservation, and calls the Payment Simulator.
5. If payment fails, the Booking Service requests a seat release.
6. If payment succeeds, the seat is confirmed and the booking record is saved.

## Testing scenarios
- Event list and unknown event behavior.
- First seat reservation succeeds; a second reservation for the same seat returns HTTP 409.
- Seat confirmation changes the state to booked.
- Releasing a reservation restores the seat to available.
- Dashboard health changes when a backend service is stopped.
- Simulated payment failure releases the seat.

## DevOps concepts demonstrated
- Docker image builds and containers.
- Docker Compose service orchestration and private networking.
- Health checks and restart policies.
- Persistent storage via named volumes.
- Automated API tests with pytest.
- Service logs and failure demonstration.

## Known limitations to disclose
This is a student demonstration, not production-ready ticketing software. Payments are simulated. The workflow has simplified compensation logic and does not implement a complete distributed transaction/saga. SQLite keeps setup simple; production would typically use a managed relational database, robust idempotency, authentication, and more complete observability.
