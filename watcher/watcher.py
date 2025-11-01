import time, os, re, requests, collections, threading

# === Configuration ===
ACCESS_LOG_PATH = "/var/log/blue-green/access.log"
ERROR_LOG_PATH = "/var/log/blue-green/error.log"

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
ERROR_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", 0.02))   # e.g. 0.02 = 2%
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 200))                   # number of recent requests to check
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 2))                 # seconds between reads
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", 30))      # avoid spam

# === Regex pattern for NGINX custom log ===
log_line = re.compile(
    r"pool=(?P<pool>\S*)\s+release=(?P<release>\S*)\s+status=(?P<status>\d+)"
)

# === Globals ===
events = collections.deque(maxlen=2000)
last_pool = None
last_alert_time = 0

# === Helper to send alert ===
def send_alert(message):
    global last_alert_time
    now = time.time()
    if now - last_alert_time < ALERT_COOLDOWN_SEC:
        return
    last_alert_time = now
    if SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=5)
        except Exception as e:
            print(f"[WARN] Slack alert failed: {e}")
    print(f"[ALERT] {message}")

# === Monitor Access Log for 5xx + Failover ===
def monitor_access_log():
    global last_pool
    print("🔍 Watching access.log for pool switch + error rate alerts...")
    with open(ACCESS_LOG_PATH, "r") as f:
        f.seek(0, 2)  # move to end of file
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
            timestamp = time.time()

            events.append((timestamp, status))

            # remove old entries
            while events and timestamp - events[0][0] > WINDOW_SIZE:
                events.popleft()

            total = len(events)
            errors = len([s for _, s in events if s >= 500])
            error_rate = errors / total if total else 0

            if error_rate > ERROR_THRESHOLD:
                send_alert(f"🚨 High error rate detected: {error_rate*100:.2f}% "
                           f"(>{ERROR_THRESHOLD*100:.0f}% threshold over {total} requests)")

            if last_pool and pool != last_pool and pool != "-":
                send_alert(f"🔄 Pool switched from {last_pool} → {pool}")
            if pool != "-":
                last_pool = pool

# === Monitor Error Log for NGINX Runtime Errors ===
def monitor_error_log():
    print("🧩 Watching error.log for runtime errors...")
    with open(ERROR_LOG_PATH, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(POLL_INTERVAL)
                continue
            if any(x in line.lower() for x in ["error", "crit", "alert", "emerg"]):
                send_alert(f"❗ NGINX error detected:\n{line.strip()}")

# === Entry point ===
if __name__ == "__main__":
    threading.Thread(target=monitor_error_log, daemon=True).start()
    monitor_access_log()
