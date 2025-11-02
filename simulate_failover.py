import os
import random
import requests
import time
import subprocess

BASE_URL = "http://localhost:8080"
TOTAL_REQUESTS = 100
ERROR_PROBABILITY = 0.9   # 90% chance to simulate errors (4xx or 5xx)
FAILOVER_TRIGGER_POINT = 80  # trigger failover near the end
DELAY = 0.1  # seconds between requests


def send_request(i):
    """Send request and simulate random failures."""
    try:
        roll = random.random()

        # --- Simulate success vs error types ---
        if roll < ERROR_PROBABILITY:
            # 50% of errors are client-side (4xx), 50% are server-side (5xx)
            if random.choice([True, False]):
                url = f"{BASE_URL}/bad-request"       # expected 4xx
            else:
                url = f"{BASE_URL}/simulate-500"      # expected 5xx
        else:
            url = f"{BASE_URL}/healthz"

        response = requests.get(url, timeout=3)
        print(f"[{i}] {url} → {response.status_code}")

    except Exception as e:
        print(f"[{i}] Exception: {e}")


def simulate_failover():
    """Simulate failover by stopping the active (blue) service."""
    print("\n🔥 Triggering simulated failure of Blue service...")
    try:
        subprocess.run(["docker", "stop", "blue_service"], check=True)
        print("✅ Blue service stopped. Nginx should reroute to Green.")
    except subprocess.CalledProcessError:
        print("⚠️ Could not stop blue_service (might already be stopped).")


def main():
    print("🚀 Starting simulation of requests with high error rate...")
    for i in range(1, TOTAL_REQUESTS + 1):
        send_request(i)

        # Trigger failover near the end of simulation
        if i == FAILOVER_TRIGGER_POINT:
            simulate_failover()

        time.sleep(DELAY)

    print("\n✅ Simulation completed. Check Slack for *High Error Rate* and *Failover* alerts.")


if __name__ == "__main__":
    main()
