import requests
import time
import json

BASE_URL = "http://localhost:8000/api"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def test_rate_limiting():
    log("--- Testing Rate Limiting ---")
    # Limit is 5 requests per minute.
    # We will send 7 requests.
    for i in range(1, 8):
        try:
            response = requests.post(f"{BASE_URL}/metrics", json={
                "timestamp": "2023-10-27T10:00:00Z",
                "value": 100,
                "type": "test_rate_limit"
            })
            if response.status_code == 201:
                log(f"Request {i}: Success (201)")
            elif response.status_code == 429:
                log(f"Request {i}: Rate Limited (429). Retry-After: {response.headers.get('Retry-After')}")
            else:
                log(f"Request {i}: Unexpected status {response.status_code}")
        except Exception as e:
            log(f"Request {i}: Error {e}")
        time.sleep(0.1)

def test_circuit_breaker():
    log("\n--- Testing Circuit Breaker ---")
    # Circuit Breaker opens after 3 failures.
    # We will try to trigger failures.
    # Since failures are random (10%), we might need many requests to trigger it, 
    # OR we can assume the user wants us to *force* it if possible, but we can't easily force it without changing env vars and restarting.
    # However, for a "manual check" I will just hit it many times and see if we get a 503.
    
    # Actually, to make this effective, I should probably increase the failure rate temporarily? 
    # Or I can just hit it 50 times, statistically it should fail enough.
    
    log("Sending requests to external-data endpoint...")
    open_circuit_seen = False
    for i in range(1, 101):
        try:
            response = requests.get(f"{BASE_URL}/external-data")
            if response.status_code == 200:
                pass # success
            elif response.status_code == 503:
                log(f"Request {i}: Circuit Breaker OPEN (503).")
                open_circuit_seen = True
                break # We found it!
            elif response.status_code == 502:
                log(f"Request {i}: External Service Failure (502). Count towards threshold.")
        except Exception as e:
            log(f"Request {i}: Error {e}")
        time.sleep(0.1)
    
    if open_circuit_seen:
        log("Circuit Breaker successfully verified!")
    else:
        log("Could not trigger Circuit Breaker (maybe failure rate is too low?).")

if __name__ == "__main__":
    # Wait for service to be up
    log("Waiting for service to be ready...")
    for _ in range(10):
        try:
            if requests.get("http://localhost:8000/health").status_code == 200:
                log("Service is up!")
                break
        except:
            time.sleep(2)
    else:
        log("Service failed to start.")
        exit(1)

    test_rate_limiting()
    test_circuit_breaker()
