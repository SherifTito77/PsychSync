# 📊 How to View the Business Dashboard

**Date**: January 21, 2026
**Status**: ✅ **Ready to Access**

---

## 🚀 Quick Start

### **Option 1: Navigate to KPI Dashboard**

1. **Start the development server**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Open your browser** to: `http://localhost:5004`

3. **Login to the application**

4. **Navigate to the KPI Dashboard**:
   - **URL**: `http://localhost:5004/analytics/kpi`
   - Or use the navigation menu and go to: **Analytics → KPI Dashboard**

---

## 📈 What You'll See

The KPI Dashboard displays business metrics organized into sections:

### **1. Acquisition Metrics**
- Trial signups
- Trial → Paid conversion rate
- Freemium → Paid rate
- Average time to purchase

### **2. Engagement Metrics**
- Monthly active users (MAU)
- Daily active users (DAU)
- Assessments per user
- Team collaboration rate
- Average session duration

### **3. Revenue Metrics**
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
- ARPU (Average Revenue Per User)
- LTV (Lifetime Value)
- Churn rate

### **4. Product Health**
- Feature usage breakdown
- Assessment completion rates
- Support ticket metrics

---

## 🔍 Real-Time Event Testing

### **View Events Being Tracked**

1. **Open Browser Developer Tools**:
   - Windows/Linux: `F12` or `Ctrl+Shift+I`
   - Mac: `Cmd+Option+I`

2. **Go to Console tab**

3. **Enable analytics logging**:
   ```javascript
   // Analytics logs are shown in development mode
   // You'll see messages like:
   // 🔄 [Analytics] Session started
   // 💰 [Analytics] Subscription trial_started: premium
   // ⭐ [Analytics] Feature used: team_optimizer_used
   ```

4. **Test event tracking manually**:
   ```javascript
   // Access the tracker
   const tracker = window.analyticsTracker;

   // Test subscription tracking
   tracker.trackSubscription('trial_started', {
     plan_tier: 'premium',
     trial_days: 14
   });

   // Test feature tracking
   tracker.trackFeatureUsed('test_feature', {
     team_size: 5
   });

   // Test session tracking
   tracker.trackSession('started', {
     entry_page: '/test'
   });

   // Grant revenue consent (to track amounts)
   tracker.grantRevenueConsent();
   ```

---

## 📊 Available Dashboards

| Dashboard | URL | Shows |
|-----------|-----|-------|
| **KPI Dashboard** | `/analytics/kpi` | Business metrics (revenue, engagement) |
| **Analytics Overview** | `/analytics` | General analytics overview |
| **Analytics Dashboard** | `/analytics/dashboard` | Main analytics dashboard |
| **Clinical Analytics** | `/analytics/clinical` | Clinical metrics |
| **Population Health** | `/analytics/population-health` | Population health metrics |
| **Predictive Analytics** | `/predictive-analytics` | AI predictions |
| **Behavioral Analytics** | `/behavioral-analytics` | User behavior patterns |

---

## 🧪 Testing the Business Events

### **Test 1: Verify Session Tracking**

1. Open the app
2. Open browser console
3. You should see:
   ```
   🔄 [Analytics] Session started
   ```

4. Refresh the page or navigate
5. Close the tab and reopen
6. You should see:
   ```
   👋 [Analytics] User returned after X days
   ```

### **Test 2: Verify Feature Tracking**

1. Navigate to: `/teams/optimizer`
2. Click "Optimize Team" button
3. In console, you should see:
   ```
   ⭐ [Analytics] Feature used: team_optimizer_used
   ```

### **Test 3: Verify Revenue Tracking**

1. Open browser console
2. Run:
   ```javascript
   // Grant consent
   window.analyticsTracker.grantRevenueConsent();

   // Track a payment
   window.analyticsTracker.trackSubscription('payment_succeeded', {
     plan_tier: 'enterprise',
     amount: 499,
     currency: 'USD',
     billing_period: 'annual'
   });
   ```

3. You should see:
   ```
   💰 [Analytics] Subscription payment_succeeded: enterprise
   ```

### **Test 4: Check Analytics Health**

1. Look for the **Analytics Health Dashboard** (fixed position, bottom-right)
2. It shows:
   - Success rate (should be ≥95%)
   - Queue size (should be low)
   - Failed events (should be 0)
   - Average delivery time

---

## 🔧 If Dashboard Shows No Data

### **Reason 1: No Events Tracked Yet**

**Solution**: Generate some test events

```javascript
// Run in browser console
const tracker = window.analyticsTracker;

// Generate 10 test subscription events
for (let i = 0; i < 10; i++) {
  tracker.trackSubscription('trial_started', {
    plan_tier: i % 3 === 0 ? 'enterprise' : i % 2 === 0 ? 'premium' : 'free',
    trial_days: 14
  });
}

// Generate 5 feature usage events
tracker.trackFeatureUsed('team_optimizer_used', { team_size: 5 });
tracker.trackFeatureUsed('assessment_taken', { assessment_type: 'Big Five' });
tracker.trackFeatureUsed('predictive_analytics_used', {});
tracker.trackFeatureUsed('clinical_tools_used', {});
tracker.trackFeatureUsed('benchmarking_used', {});

console.log('✅ Test events generated!');
```

### **Reason 2: Backend Not Processing Events**

**Check**:
1. Open Network tab in DevTools
2. Filter by "analytics"
3. Look for POST requests to `/api/v1/analytics/track`
4. Check if they return 200 OK

**If failing**: Check if backend is running:
```bash
# Check if backend is up
curl http://localhost:8000/api/v1/health

# Should return: {"status": "healthy"}
```

### **Reason 3: Events Not Being Aggregated**

The KPI Dashboard uses `kpiService` which aggregates raw events into metrics. This may need:

1. **Backend aggregation endpoint**: `/api/v1/analytics/kpi`
2. **Scheduled aggregation job**: Run every hour/day
3. **Materialized views**: For fast queries

**Temporary Solution**: The dashboard may show mock data until aggregation is implemented.

---

## 📱 Mobile Access

The dashboards are fully responsive! Access them from any device:

1. **Mobile browser**: Navigate to `http://your-server:5004/analytics/kpi`
2. **Responsive design**: Dashboards adapt to screen size
3. **Touch-friendly**: All charts are interactive

---

## 🎨 Dashboard Customization

### **Change Time Period**

The KPI Dashboard supports different time periods:
- **30 days**: Last month
- **90 days**: Last quarter
- **12 months**: Last year

Click the period selector to switch views.

### **Export Data**

Most dashboards support data export:
- **CSV**: For spreadsheet analysis
- **JSON**: For API consumption
- **PDF**: For reports

Look for the "Export" button on each dashboard.

---

## 📊 Understanding the Metrics

### **Key Performance Indicators (KPIs)**

| Metric | Formula | What It Tells You |
|--------|---------|------------------|
| **MRR** | Sum of monthly subscriptions | Monthly revenue |
| **ARR** | MRR × 12 | Annualized revenue |
| **Churn Rate** | Cancelled MRR / Starting MRR | Customer loss rate |
| **LTV** | ARPU / Churn Rate | Customer lifetime value |
| **CAC** | Marketing Spend / New Customers | Cost to acquire customer |
| **LTV:CAC** | LTV / CAC | Payback period (should be >3) |
| **DAU/MAU** | Daily users / Monthly users | Engagement stickiness |
| **ARPU** | Total MRR / Total Users | Revenue per customer |

### **Healthy Ranges**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| **Churn Rate** | <5% | 5-10% | >10% |
| **LTV:CAC** | >3 | 2-3 | <2 |
| **DAU/MAU** | >20% | 10-20% | <10% |
| **Trial → Paid** | >15% | 10-15% | <10% |

---

## 🔗 Quick Links

- **KPI Dashboard**: [http://localhost:5004/analytics/kpi](http://localhost:5004/analytics/kpi)
- **Analytics Overview**: [http://localhost:5004/analytics](http://localhost:5004/analytics)
- **Analytics Dashboard**: [http://localhost:5004/analytics/dashboard](http://localhost:5004/analytics/dashboard)

---

## ✅ Checklist

Before viewing the dashboard:

- [ ] Development server running (`npm run dev`)
- [ ] Logged into the application
- [ ] Backend API running (`uvicorn app.main:app`)
- [ ] Browser console open (to see event logs)
- [ ] Navigated to `/analytics/kpi`

**Expected Result**: KPI Dashboard loads and shows business metrics!

---

**Last Updated**: January 21, 2026
**Need Help?** Check the browser console for error messages
