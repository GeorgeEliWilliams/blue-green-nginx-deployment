import time, os, re, requests, json, collections, threading

LOG_PATH = "/var/log/nginx/access.log"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
ERROR_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", 0.2))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 30))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 2))

log_line = re.compile(
    r"pool=(?P<pool>\S*)\s+release=(?P<release>\S*)\s+status=(?P<status>\d+)"
)

# Store recent results
events = collections.deque(maxlen=1000)
last_pool = None
last_alert_time = 0

def send_alert(message):
    global last_alert_time
    now = time.time()
    if now - last_alert_time < 30:  # rate-limit: 30 s
        return
    last_alert_time = now
    if SLACK_WEBHOOK:
        requests.post(SLACK_WEBHOOK, json={"text": message})
    print(f"[ALERT] {message}")

def monitor():
    global last_pool
    print("🔍 Watching logs...")
    with open(LOG_PATH, "r") as f:
        f.seek(0, 2)  # go to end of file
        while True:
            line = f.readline()
            if not line:
                time.sleep(POLL_INTERVAL)
                continue

            m = log_line.search(line)
            if not m:
                continue

            pool = m.group("pool")
            status = int(m.group("status"))

            # Track error stats
            timestamp = time.time()
            events.append((timestamp, status))

            # Remove old events outside window
            while events and timestamp - events[0][0] > WINDOW_SIZE:
                events.popleft()

            # Calculate error rate
            total = len(events)
            errors = len([s for _, s in events if s >= 500])
            error_rate = errors / total if total else 0

            if error_rate > ERROR_THRESHOLD:
                send_alert(f"🚨 High error rate detected: {error_rate*100:.1f}%")

            # Detect pool flip
            if last_pool and pool != last_pool and pool != "-":
                send_alert(f"🔄 Pool switched from {last_pool} to {pool}")
            if pool != "-":
                last_pool = pool

if __name__ == "__main__":
    monitor()
