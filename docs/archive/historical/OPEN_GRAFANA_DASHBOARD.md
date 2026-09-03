# 🚀 How to Open the Grafana Dashboard

**Quick Guide:** 3 steps to view your async cache monitoring dashboard

---

## Option 1: Using Docker (RECOMMENDED - Easiest)

### Step 1: Start the Monitoring Stack

```bash
# Start Grafana, Prometheus, and Redis Exporter
docker-compose -f docker-compose.monitoring.yml up -d grafana prometheus redis-exporter

# Wait for services to start (about 10 seconds)
sleep 10
```

**What this does:**
- Starts Grafana on port 3001
- Starts Prometheus on port 9090
- Starts Redis Exporter on port 9121

### Step 2: Open Grafana in Your Browser

```
http://localhost:3001
```

**Login credentials:**
- Username: `admin`
- Password: `admin` (or check your GRAFANA_PASSWORD env var)

### Step 3: Import the Dashboard

1. In Grafana, click the **"+"** icon in the left sidebar
2. Click **"Import"**
3. Click **"Upload JSON file"**
4. Navigate to: `deploy/grafana/dashboards/redis-cache-dashboard.json`
5. Click **"Import"**

**That's it!** You should now see the async cache dashboard with 8 panels showing:
- Cache hit rate
- Cache hits vs misses
- Memory usage
- Response times
- And more!

---

## Option 2: Quick Docker Commands

```bash
# Start only Grafana (quickest)
docker-compose -f docker-compose.monitoring.yml up -d grafana

# Open in browser
open http://localhost:3001  # macOS
# or
xdg-open http://localhost:3001  # Linux
# or
start http://localhost:3001  # Windows
```

---

## Option 3: Native Installation (Without Docker)

If you prefer to install Grafana natively:

### macOS
```bash
# Install Grafana
brew install grafana

# Start Grafana
brew services start grafana

# Open in browser
open http://localhost:3000
```

### Linux
```bash
# Install Grafana
sudo apt-get install -y apt-transport-https
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Open in browser
xdg-open http://localhost:3000
```

---

## 🎯 What You Should See

Once the dashboard is loaded, you'll see **8 panels**:

1. **Cache Hit Rate** - Shows % of cache hits (target: >70%)
2. **Cache Hits vs Misses** - Compares hits/misses per second
3. **Total Commands Processed** - Redis throughput
4. **Connected Clients** - Active connections to Redis
5. **Memory Usage** - Redis memory consumption
6. **Cache Key Count** - Number of cached items
7. **Expired Keys** - Cache evictions over time
8. **Response Time (P95)** - API latency percentiles

---

## 🔍 Verifying It's Working

### Check Services Are Running

```bash
# Check Grafana is running
curl http://localhost:3001/api/health

# Check Prometheus is running
curl http://localhost:9090/-/healthy

# Check Redis Exporter is running
curl http://localhost:9121/metrics | grep redis_keyspace
```

### Check Dashboard Has Data

In the Grafana dashboard:
1. Look at the top right - set time range to "Last 5 minutes"
2. Panels should show graphs with data
3. If no data, check Prometheus targets: http://localhost:9090/targets

---

## 🛠️ Troubleshooting

### Issue: Can't Access Grafana

**Solution:**
```bash
# Check if container is running
docker ps | grep grafana

# Check logs
docker logs psychsync-grafana

# Restart if needed
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### Issue: Dashboard Shows "No Data"

**Solution:**
1. Check Prometheus is scraping: http://localhost:9090/targets
2. Verify Redis Exporter is running: http://localhost:9121/metrics
3. Check data source in Grafana:
   - Go to Configuration → Data Sources → Prometheus
   - Click "Test" - should show green "Data source is working"

### Issue: Port Already in Use

**Solution:**
```bash
# Check what's using the port
lsof -i :3001

# Either stop the other service or change Grafana port in docker-compose.monitoring.yml:
# Change "3001:3000" to "3002:3000"
```

---

## 📊 Quick Verification Commands

```bash
# 1. Check all monitoring services
docker-compose -f docker-compose.monitoring.yml ps

# 2. Check Grafana logs
docker logs psychsync-grafana --tail 50

# 3. Check Prometheus logs
docker logs psychsync-prometheus --tail 50

# 4. Check Redis Exporter metrics
curl http://localhost:9121/metrics | grep keyspace

# 5. Test Prometheus query
curl http://localhost:9090/api/v1/query?query=up
```

---

## 🎓 Learning Resources

Once you have Grafana open:

1. **Explore the Dashboard**
   - Hover over panels to see values
   - Click panel titles to edit
   - Drag panels to rearrange

2. **Create Your Own Queries**
   - Click panel title → Edit
   - Try queries like:
     - `rate(redis_keyspace_hits_total[5m])`
     - `redis_memory_used_bytes`

3. **Set Up Alerts**
   - Click panel title → Alert
   - Set conditions (e.g., "Hit Rate < 70%")
   - Configure notifications

---

## ✅ Success Checklist

- [ ] Docker monitoring stack running
- [ ] Grafana accessible at http://localhost:3001
- [ ] Logged in to Grafana (admin/admin)
- [ ] Dashboard imported (redis-cache-dashboard.json)
- [ ] Panels showing data (not "No Data")
- [ ] Time range set to "Last 5 minutes" or "Last 1 hour"

---

## 🚀 Next Steps

After opening the dashboard:

1. **Monitor for 24 hours** - See patterns in your cache usage
2. **Optimize TTL values** - Adjust cache expiration times
3. **Set up alerts** - Get notified when hit rate drops
4. **Create additional dashboards** - Monitor specific endpoints

---

**Quick Start:**
```bash
# One command to start everything
docker-compose -f docker-compose.monitoring.yml up -d grafana prometheus redis-exporter

# Open in browser
open http://localhost:3001
```

**Need Help?** Check the detailed guide: `deploy/grafana/SETUP_CACHE_MONITORING.md`
