# 📊 Local Monitoring Guide (No Docker, No Limits!)

## Overview
Monitor your PsychSync application locally with **unlimited retention** and **no external dependencies**. All tools work with your existing `/metrics` endpoint.

---

## 🚀 Quick Start Options

### **Option 1: Browser Dashboard** ⭐ **EASIEST**

Just open the HTML file in your browser:

```bash
# Open in browser (Mac)
open metrics_dashboard.html

# Or double-click the file in Finder
```

**Features:**
- ✅ Beautiful real-time dashboard
- ✅ Auto-refreshes every 5 seconds
- ✅ No installation required
- ✅ Works in any modern browser
- ✅ **Unlimited retention** (view as long as you want!)

**URL:** `file:///Users/sheriftito/Downloads/psychsync/metrics_dashboard.html`

---

### **Option 2: Terminal Monitor**

Watch metrics in your terminal:

```bash
./watch_metrics.sh
```

**Features:**
- ✅ Real-time updates every 5 seconds
- ✅ Shows key metrics at a glance
- ✅ Zero dependencies
- ✅ Works over SSH
- ✅ Press Ctrl+C to stop

---

### **Option 3: CSV Logger** 📝 **FOR HISTORICAL DATA**

Record metrics to CSV files for analysis:

```bash
# Start logging (records every 60 seconds)
python metrics_logger.py

# Metrics saved to: metrics_history/metrics_YYYYMMDD.csv
```

**Features:**
- ✅ **Unlimited retention** (stored as CSV files)
- ✅ Open in Excel, Google Sheets, Numbers
- �- Analyze trends over time
- ✅ Create your own charts
- ✅ Export to any format
- ✅ Only ~1KB per day (very small!)

**View in Excel/Numbers:**
```bash
open metrics_history/
```

---

## 📈 What You Can Do With CSV Data

### **View in Spreadsheet Software**
```bash
# Mac (opens in default app)
open metrics_history/metrics_20250210.csv

# Or import into Excel/Google Sheets manually
```

### **Analyze Trends**
- Day-over-day request growth
- Peak usage times
- Error rate trends
- Database connection patterns
- Cache effectiveness over time

### **Create Custom Charts**
Import into your favorite tool:
- Excel charts
- Google Sheets
- Python (matplotlib/pandas)
- R
- Any charting tool

---

## 🎯 Recommended Setup

### **For Daily Development:**
1. **Keep `metrics_dashboard.html` open** in a browser tab
2. Check it occasionally to see current metrics
3. No setup, no maintenance

### **For Long-Term Analysis:**
1. **Run `metrics_logger.py`** in the background:
   ```bash
   # Start in background
   python metrics_logger.py &

   # Or use screen/tmux for persistent sessions
   screen -S metrics
   python metrics_logger.py
   # Press Ctrl+A, D to detach
   ```

2. **Review CSV files weekly:**
   ```bash
   open metrics_history/
   ```

---

## 📂 File Locations

```
psychsync/
├── metrics_dashboard.html      # Browser dashboard
├── watch_metrics.sh             # Terminal monitor
├── metrics_logger.py            # CSV logger
└── metrics_history/             # CSV data files (auto-created)
    └── metrics_20250210.csv
```

---

## 🔧 Customization

### **Change Refresh Interval**

**Browser Dashboard:**
Edit `metrics_dashboard.html` line ~300:
```javascript
const REFRESH_INTERVAL = 10000; // Change to 10 seconds
```

**Terminal Monitor:**
Edit `watch_metrics.sh` line ~48:
```bash
sleep 10  # Change from 5 to 10 seconds
```

**CSV Logger:**
Edit `metrics_logger.py` line ~16:
```python
INTERVAL_SECONDS = 120  # Change to 2 minutes
```

### **Add More Metrics to Dashboard**

Edit `metrics_dashboard.html` and add to the `metrics-grid` section:
```html
<div class="metric-card">
    <div class="metric-label">Your Metric</div>
    <div class="metric-value" id="yourMetric">-</div>
    <div class="metric-unit">Description</div>
</div>
```

Then add the JavaScript to fetch it:
```javascript
document.getElementById('yourMetric').textContent = formatNumber(
    getMetricValue(metricsText, 'psychsync_your_metric_name')
);
```

---

## 💡 Tips

1. **Disk Space**: CSV files are tiny (~1KB per recording). A year of data = ~500KB
2. **Performance**: CSV logging has negligible impact on your app
3. **Privacy**: All data stays on your machine
4. **Portability**: Move CSV files anywhere, analyze on any computer
5. **Backup**: Just copy the `metrics_history` folder

---

## 🆚 Comparison with Grafana Cloud

| Feature | Local Tools | Grafana Cloud |
|---------|-------------|---------------|
| **Retention** | ✅ **Unlimited** | ❌ 14 days only |
| **Setup** | ✅ 5 seconds | ⚠️ 5 minutes |
| **Docker Required** | ✅ **No** | ❌ Yes (for self-hosted) |
| **Internet Required** | ✅ **No** | ✅ Yes |
| **Privacy** | ✅ 100% local | ⚠️ Cloud-hosted |
| **Cost** | ✅ **Free forever** | ⚠️ Free (limited) |
| **Customization** | ✅ Edit HTML/Python | ⚠️ UI-based only |
| **Alerts** | ❌ Manual | ✅ Built-in |
| **Sharing** | ⚠️ Manual files | ✅ Share links |

---

## 🎓 Example: Find Peak Usage Time

1. Let metrics_logger.py run for a day
2. Open the CSV in Excel/Numbers
3. Create a pivot chart:
   - Rows: `timestamp` (group by hour)
   - Values: `http_requests_total`
4. Instantly see your peak usage hours!

---

## 📚 Advanced Analysis (Optional)

### **Using Python for Analysis**

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load metrics
df = pd.read_csv('metrics_history/metrics_20250210.csv')

# Plot requests over time
plt.figure(figsize=(12, 6))
plt.plot(pd.to_datetime(df['timestamp']), df['http_requests_total'])
plt.title('HTTP Requests Over Time')
plt.xlabel('Time')
plt.ylabel('Total Requests')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('requests_over_time.png')
plt.show()
```

---

## ✅ Summary

**Your local monitoring setup is:**
- ✅ **Complete** - All metrics being collected
- ✅ **Unlimited** - No retention limits
- ✅ **Private** - Data never leaves your machine
- ✅ **Free** - No costs whatsoever
- ✅ **Simple** - No complex setup required

**You have everything you need for local development monitoring!**

---

**Questions?**
- Check the metrics directly: `curl http://localhost:8000/metrics`
- Review CSV files: `open metrics_history/`
- Open dashboard: `open metrics_dashboard.html`
