# Blue-Green Deployment with Nginx Failover

This project demonstrates a **Blue-Green Deployment** setup using Docker Compose and Nginx as a reverse proxy with automatic failover.  
The goal is to ensure **zero failed requests** during deployment rollouts or application failures by routing traffic between Blue and Green environments seamlessly.

---

## 🧠 Overview

In this setup:
- Two identical application environments (`blue` and `green`) run simultaneously.
- Nginx acts as a **smart traffic router**, forwarding client requests to the active environment.
- If the active environment fails (due to crash or chaos injection), Nginx automatically redirects traffic to the standby environment.

---

## 🧩 Components

| Component | Description |
|------------|-------------|
| **Blue Service** | Active version of the application (`blue_service`) |
| **Green Service** | Standby version, used during failover (`green_service`) |
| **Nginx Proxy** | Routes requests and handles failover logic |
| **`.env` file** | Defines environment variables like image names and release IDs |

---

## ⚙️ Configuration

All dynamic values are stored in the `.env` file for flexibility.  
You can rename `.env.example` to `.env` and update it as needed.

Example `.env`:

```bash
BLUE_IMAGE=myapp:blue
GREEN_IMAGE=myapp:green
RELEASE_ID_BLUE=1.0.0
RELEASE_ID_GREEN=1.0.1
ACTIVE_POOL=blue
```