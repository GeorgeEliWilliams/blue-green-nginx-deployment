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