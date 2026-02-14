# Resilient Analytics API

A robust backend API for a simulated real-time analytics service, featuring Redis caching, rate limiting, and circuit breaker patterns. Built with FastAPI and Docker.

## Features

-   **Metric Ingestion**: High-throughput endpoint for receiving metrics.
-   **Metric Summaries**: Aggregated views of metrics with **Redis Caching** for performance.
-   **Rate Limiting**: Protects the ingestion endpoint from abuse using detailed **Redis-based** rate limiting (Fixed Window).
-   **Circuit Breaker**: Resilient integration with a simulated flaky external service, implementing **Closed**, **Open**, and **Half-Open** states.
-   **Dockerized**: Fully containerized application and Redis database.

## Prerequisites

-   Docker and Docker Compose

## Setup & Running

1.  Clone the repository.

    ```bash
    git clone https://github.com/Vyshnavichakkapalli/Resilient-Analytics-API-with-Redis-Caching-Rate-Limiting-and-Circuit-Breaker
    cd Resilient-Analytics-API-with-Redis-Caching-Rate-Limiting-and-Circuit-Breaker
2.  Start the services using Docker Compose:

    ```bash
    docker-compose up --build
    ```

    The API will be available at `http://localhost:8000`.

## API Documentation

### 1. Ingest Metric

-   **Endpoint**: `POST /api/metrics`
-   **Description**: Ingest a new metric data point.
-   **Rate Limit**: 5 requests per minute per IP.
-   **Payload**:
    ```json
    {
      "timestamp": "2023-10-27T10:00:00Z",
      "value": 100.5,
      "type": "cpu_usage"
    }
    ```
-   **Response**: `201 Created`

### 2. Get Metric Summary

-   **Endpoint**: `GET /api/metrics/summary`
-   **Description**: Retrieve aggregated metrics (average) for a specific type. Cached for 60 seconds.
-   **Query Parameters**:
    -   `type`: string (e.g., `cpu_usage`)
    -   `period`: string (default: `daily`)
-   **Response**: `200 OK`
    ```json
    {
      "type": "cpu_usage",
      "period": "daily",
      "average_value": 75.2,
      "count": 150
    }
    ```

### 3. Get External Data (Simulated)

-   **Endpoint**: `GET /api/external-data`
-   **Description**: Fetches data from a simulated external service to demonstrate the Circuit Breaker.
-   **Behavior**:
    -   Randomly fails based on `EXTERNAL_SERVICE_FAILURE_RATE` (default 10%).
    -   If failures exceed threshold, circuit opens and returns `503 Service Unavailable` immediately.
    -   After timeout, allows a test request (Half-Open).
-   **Response**: `200 OK` or `503 Service Unavailable`.

## Resilience Patterns

### Caching
Implemented using Redis. key: `summary:{type}:{period}`. TTL: 60 seconds.
Strategy: Cache-Aside (Check Cache -> Miss -> Compute -> Set Cache).

### Rate Limiting
Implemented using Redis `INCR` and `EXPIRE`. Protocol: Fixed Window Counter.
Limit: 5 requests / 60 seconds.
Headers: `Retry-After` is sent on 429 responses.

### Circuit Breaker
In-memory state machine protecting `fetch_risky_external_data`.
States:
-   **Closed**: Normal operation.
-   **Open**: Fast failure after threshold (3 failures) reached. Reset timeout: 10s.
-   **Half-Open**: Allows one test request after timeout. Success closes circuit; failure re-opens it.

## Testing

To run the test suite, you can run `pytest` within the container or locally if dependencies are installed.

```bash
# Running tests inside the container
docker-compose run app pytest
```

Tests cover:
-   Unit tests for `RateLimiter` and `CircuitBreaker` logic.
-   Integration tests for API endpoints and resilience behaviors.