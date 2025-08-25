# WebHealth – AWS Lambda + CDK (Python)

This project demonstrates **Step-1 and Step-2 combined**:  

- **Step-1:** CanaryFn Lambda that checks a single website and publishes metrics (Availability & Latency) to CloudWatch.  
- **Step-2:** Extended CanaryFn to support **multiple URLs** and added a CloudWatch **Dashboard** for visualization.  

---

##  Step-1: Single URL Canary
- Lambda `CanaryFn` checks one website (`https://www.google.com`).  
- Publishes custom metrics into **CloudWatch (WebHealth namespace)**.  
- Triggered every 5 minutes by EventBridge.  

**Evidence (Screenshots for report):**  
- CloudWatch → Metrics → WebHealth → Availability + Latency (for Google)  
- CloudWatch → Logs → CanaryFn log stream  

---

##  Step-2: Multi-URL + Dashboard
- Canary now monitors multiple websites (`https://www.python.org`, `https://www.google.com`, `https://www.github.com`).  
- CloudWatch **Dashboard** added to visualize Availability & Latency for all sites.  

**Evidence (Screenshots for report):**  
- Dashboard “WebHealth” visible in CloudWatch  
- Metrics show separate dimensions for each URL  
- Lambda Configuration → Environment Variables (showing `URLS`)  

---

## 🚀 Deploy
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# First time only
cdk bootstrap

# Build and deploy
cdk synth
cdk deploy
