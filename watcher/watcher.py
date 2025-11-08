import os
import time
import re
import logging
import requests
from collections import deque

#  Logging Setup 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

#  Environment Variables 
LOG_FILE_PATH = "/var/log/blue-green/access.log"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Adjustable thresholds (use low values for testing)
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", "0.01"))  # 1%
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "20"))  # recent N requests
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "1"))  # check logs every second
ALERT_COOLDOWN = int(os.getenv("ALERT_COOLDOWN", "60"))  # seconds before next alert

#  State Tracking 
recent_statuses = deque(maxlen=WINDOW_SIZE)
last_alert_time = 0
last_pool = None
alert_active = False  # used for recovery detection

#  Slack Notification 
def send_slack_alert(message):
    """Send formatted message to Slack via webhook."""
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        if response.status_code != 200:
            logging.error(f"Slack webhook returned {response.status_code}: {response.text}")
        else:
            logging.info("✅ Alert sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send Slack alert: {e}")

#  Log Parser 
def parse_log_line(line):
    """
    Extract pool, release, and HTTP status from access log line.
    Example line:
    pool=blue release=v1.0.0 status=200 upstream_status=200
    """
    match = re.search(r"pool=(\w+).*release=(v[\d\.]+).*status=(\d+)", line)
    if match:
        pool, release, status = match.groups()
        return pool, release, int(status)
    return None, None, None

#  Watcher Logic 
def monitor_logs():
    global last_pool, last_alert_time, alert_active

    logging.info("👀 Watcher started: monitoring Nginx access.log for errors and failovers...")
    logging.info(f"Threshold: {ERROR_RATE_THRESHOLD*100:.2f}% | Window size: {WINDOW_SIZE} | Poll: {POLL_INTERVAL}s")

    with open(LOG_FILE_PATH, "r") as f:
        f.seek(0, 2)  # Move to end of file

        while True:
            line = f.readline()

            if not line:
                time.sleep(POLL_INTERVAL)
                continue

            pool, release, status = parse_log_line(line)
            if not pool or not status:
                continue

            recent_statuses.append(status)

            #  Detect Failover (pool switch) 
            if last_pool and pool != last_pool:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                message = (
                    "*Failover Event Detected*\n"
                    ":arrows_counterclockwise: **Failover Detected**\n"
                    f"Previous Pool: *{last_pool.upper()}* → Current Pool: *{pool.upper()}*\n"
                    ":warning: *Action Required:* Check the health of the previous pool.\n"
                    f"Timestamp: `{timestamp}`\n"
                    "_DevOps Monitoring | Blue-Green Deployment_"
                )
                send_slack_alert(message)
                logging.info(f"⚠️ Failover detected: {last_pool} → {pool}")
            last_pool = pool

            #  Error Rate Detection 
            if len(recent_statuses) == WINDOW_SIZE:
                error_count = sum(1 for s in recent_statuses if s >= 500)
                error_rate = error_count / WINDOW_SIZE
                now = time.time()

                logging.info(f"🧮 Checking error rate: {error_count}/{WINDOW_SIZE} errors ({error_rate*100:.2f}%)")

                # High error rate alert
                if error_rate > ERROR_RATE_THRESHOLD and (now - last_alert_time > ALERT_COOLDOWN):
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    message = (
                        "*Blue/Green Alert - ERROR_RATE*\n"
                        ":chart_with_upwards_trend: **High Error Rate Alert!**\n"
                        f"• Error Rate: {error_rate*100:.2f}% (Threshold: {ERROR_RATE_THRESHOLD*100:.2f}%)\n"
                        f"• Errors: {error_count}/{WINDOW_SIZE} requests\n"
                        f"• Current Pool: *{pool.upper()}*\n"
                        f"• Window Size: {WINDOW_SIZE} requests\n"
                        ":warning: **Action Required:** Investigate upstream logs and consider manual failover.\n"
                        f"Timestamp: `{timestamp}`\n"
                        "_DevOps Monitoring | Blue-Green Deployment_"
                    )
                    send_slack_alert(message)
                    logging.warning(f"🚨 High error rate detected: {error_rate*100:.2f}% on {pool}")
                    last_alert_time = now
                    alert_active = True
                    recent_statuses.clear()

                # Recovery detection (system stabilizes)
                elif alert_active and error_rate <= ERROR_RATE_THRESHOLD:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    message = (
                        "*Recovery Notice*\n"
                        ":white_check_mark: **Error Rate Back to Normal**\n"
                        f"• Current Pool: *{pool.upper()}*\n"
                        f"• Error Rate: {error_rate*100:.2f}% (Below Threshold)\n"
                        f"Timestamp: `{timestamp}`\n"
                        "_DevOps Monitoring | Blue-Green Deployment_"
                    )
                    send_slack_alert(message)
                    logging.info(f"✅ Error rate recovered to normal: {error_rate*100:.2f}% on {pool}")
                    alert_active = False

#  Entrypoint 
if __name__ == "__main__":
    try:
        monitor_logs()
    except KeyboardInterrupt:
        logging.info("Watcher stopped by user.")
    except Exception as e:
        logging.exception(f"Watcher crashed: {e}")
