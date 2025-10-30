# 🧭 Runbook: Blue/Green Nginx Deployment Alerts & Operator Actions

This runbook provides guidance on interpreting system alerts and the corresponding operational actions required to maintain service reliability in the Blue/Green deployment setup.

---

## 📘 Overview

Our Blue/Green deployment uses **Nginx as a reverse proxy** to route traffic between two Node.js environments — **Blue** (current production) and **Green** (staging or next release).  
A **monitoring script** continuously checks health endpoints and sends **Slack alerts** when errors exceed a configured threshold.

---

## 🚨 Alert Types and Meanings

### 1. **High Error Rate Alert**
**Message Example:**  
> `⚠️ ALERT: High error rate detected! Error rate 0.35 exceeds threshold 0.2.`

**Meaning:**  
The active service (Blue or Green) is returning too many failed responses (HTTP 5xx or 4xx).  

**Actions to Take:**
1. Check which pool is active:
```bash
 echo $ACTIVE_POOL
```

2. Confirm service health
 ```bash
 curl http://localhost:8080/health
```

Verify successful switch:
```bash
curl http://localhost:8080/
```

2. Service Down Alert
**Message Example:**  
> `🚨 CRITICAL: Active service blue_service is unreachable.`

Meaning:
Nginx or the backend container failed health checks — requests are not being served.

Actions to Take:

1. Inspect logs:
```bash
docker logs nginx_proxy
docker logs blue_service
docker logs green_service
```

2. Restart the affected service

Slack Webhook or Notification Failure

**Message Example:**  
> `❗ Warning: Slack notification failed. Check webhook URL or network.`

Meaning:
The monitoring script failed to send alerts due to a misconfigured or invalid Slack webhook.

Troubleshooting Tips

Nginx startup error:

“worker_processes directive is not allowed here”

Remove the worker_processes directive from /nginx/conf.d/default.conf (belongs in nginx.conf, not site config).

No Slack alerts appearing:

Verify Slack app is active in the workspace.

Check if alert_watcher container is running: