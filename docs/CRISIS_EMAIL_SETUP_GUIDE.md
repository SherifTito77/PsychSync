# Crisis Email Notification Setup Guide

**Purpose:** Configure SMTP for automated crisis intervention emails

**⚠️ CRITICAL:** Crisis emails must be delivered reliably. Lives depend on it.

---

## 📧 SMTP Configuration Options

### **Option 1: SendGrid (Recommended for Production)**
**Pros:** High deliverability, HIPAA-compliant, excellent API
**Cons:** Costs money ($10-100/month depending on volume)
**Setup Time:** 15 minutes

```bash
# Add to .env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=apikey
SMTP_PASSWORD=SG.YOUR_SENDGRID_API_KEY_HERE
EMAILS_FROM_EMAIL=crisis-alerts@psychsync.ai
EMAILS_FROM_NAME=PsychSync Crisis Team
ENABLE_EMAIL_VERIFICATION=true
```

**Get API Key:**
1. Sign up at https://sendgrid.com/
2. Create API Key with "Mail Send" permissions
3. Verify sender domain (crisis-alerts@yourdomain.com)

---

### **Option 2: AWS SES (Cost-Effective for Scale)**
**Pros:** Very cheap ($0.10/1000 emails), HIPAA-eligible
**Cons:** Requires AWS account, more complex setup
**Setup Time:** 30 minutes

```bash
# Add to .env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=YOUR_AWS_SES_SMTP_USERNAME
SMTP_PASSWORD=YOUR_AWS_SES_SMTP_PASSWORD
EMAILS_FROM_EMAIL=crisis-alerts@psychsync.ai
EMAILS_FROM_NAME=PsychSync Crisis Team
ENABLE_EMAIL_VERIFICATION=true
```

**Get Credentials:**
1. AWS Console → SES → SMTP Settings
2. Create SMTP credentials
3. Verify sender identity (domain or email)

---

### **Option 3: Gmail (Development/Testing Only)**
**Pros:** Free, easy setup
**Cons:** Not HIPAA-compliant, low limits (500/day), security risks
**Setup Time:** 10 minutes

```bash
# Add to .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password_here
EMAILS_FROM_EMAIL=your@gmail.com
EMAILS_FROM_NAME=PsychSync Testing
ENABLE_EMAIL_VERIFICATION=true
```

**Get App Password:**
1. Google Account → Security → 2-Step Verification
2. App passwords → Generate → "Mail"
3. Use 16-character password

**⚠️ WARNING:** Gmail is NOT HIPAA-compliant. Only use for testing!

---

### **Option 4: Mailgun (Good Balance)**
**Pros:** Good deliverability, HIPAA available, reasonable pricing
**Cons:** More expensive than SendGrid
**Setup Time:** 20 minutes

```bash
# Add to .env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=postmaster@mg.yourdomain.com
SMTP_PASSWORD=YOUR_MAILGUN_PASSWORD
EMAILS_FROM_EMAIL=crisis-alerts@mg.yourdomain.com
EMAILS_FROM_NAME=PsychSync Crisis Team
ENABLE_EMAIL_VERIFICATION=true
```

---

## 🔧 Setup Instructions

### **Step 1: Choose SMTP Provider**

**For Development:**
- Use Gmail (Option 3) - Free and easy

**For Production:**
- Use SendGrid (Option 1) - Best balance of cost/reliability
- Use AWS SES (Option 2) - Cheapest for high volume

---

### **Step 2: Update Environment Variables**

Edit `.env` file:

```bash
# SMTP Configuration
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=your_username
SMTP_PASSWORD=your_password_or_api_key

# Crisis Email Configuration
EMAILS_FROM_EMAIL=crisis-alerts@psychsync.ai
EMAILS_FROM_NAME=PsychSync Crisis Team

# Enable Email
ENABLE_EMAIL_VERIFICATION=true
```

---

### **Step 3: Verify Configuration**

```bash
# Restart backend server
pkill -f "uvicorn app.main:app"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### **Step 4: Test Email Delivery**

```bash
# Run email test script
python3 tests/test_crisis_email.py
```

Expected output:
```
✅ SMTP connection successful
✅ Email sent to test@example.com
✅ Check inbox for test email
```

---

## 📝 Email Templates

### **Crisis Alert Email (Level 1 - Critical)**

**Subject:** 🚨 URGENT: Crisis Intervention Required

**Body:**
```
 IMMEDIATE ACTION REQUIRED

A user has screened positive for critical suicide risk.

User: {user_name}
Email: {user_email}
Organization: {org_name}
Time: {timestamp}
Risk Level: CRITICAL

DETAILS:
{alert_details}

IMMEDIATE ACTIONS:
1. Attempt to contact user by phone
2. Check if user is in immediate danger
3. If imminent danger → Call 911
4. Contact emergency services if needed

CRISIS RESOURCES:
• 988 Suicide & Crisis Lifeline
• Crisis Text Line: Text HOME to 741741
• Emergency: 911

Log into dashboard for full details: {dashboard_link}

⚠️ This is an automated crisis alert. Response time is CRITICAL.
```

---

### **High Risk Email (Level 2 - High)**

**Subject:** ⚠️ Mental Health Intervention Required

**Body:**
```
HIGH RISK ALERT

A user has screened positive for elevated suicide risk.

User: {user_name}
Email: {user_email}
Organization: {org_name}
Time: {timestamp}
Risk Level: HIGH

ACTION REQUIRED:
• Contact user within 2 hours
• Conduct safety assessment
• Determine if in-person evaluation needed

Resources and recommendations have been sent to user.

Log into dashboard for full details: {dashboard_link}
```

---

### **User Crisis Notification**

**Subject:** Support Resources Available

**Body:**
```
Hi {user_name},

Based on your recent assessment, we want to share some resources with you.

You are not alone. Support is available 24/7.

IMMEDIATE SUPPORT:
• 988 Suicide & Crisis Lifeline (Call or Text 988)
• Crisis Text Line: Text HOME to 741741
• Emergency Services: 911

ONLINE RESOURCES:
• https://findahelpline.com/ - Find helplines in your country
• https://psychsync.com/crisis - Crisis resources and tools

RECOMMENDED NEXT STEPS:
1. Reach out to one of the resources above
2. Contact a mental health professional
3. Talk to someone you trust

{additional_resources}

You don't have to face this alone.

With care,
The PsychSync Team
```

---

## ⚠️ Critical Configuration Requirements

### **Deliverability**

1. **SPF Record:**
```dns
psychsync.com. IN TXT "v=spf1 include:sendgrid.net ~all"
```

2. **DKIM Signature:**
- Setup DKIM in your DNS (provider will give you the record)

3. **DMARC Policy:**
```dns
_dmarc.psychsync.com. IN TXT "v=DMARC1; p=none; rua=mailto:dmarc@psychsync.com"
```

---

### **Reliability**

1. **Fallback SMTP:** Configure secondary SMTP provider
2. **Queue Management:** Enable retries for failed sends
3. **Monitoring:** Alert on email delivery failures
4. **Logging:** Log all email send attempts

---

### **Security (HIPAA)**

1. **Encryption:** TLS required for all emails
2. **Access Control:** Restrict SMTP credentials
3. **Audit:** Log all email access
4. **BAA:** Have BAA with email provider (SendGrid, AWS SES)

---

## 🧪 Testing Checklist

### **Pre-Production Testing**

- [ ] Send test email to personal inbox
- [ ] Verify crisis email format is clear
- [ ] Test email delivery to spam folder
- [ ] Test with invalid email (should handle gracefully)
- [ ] Test email throttling (send 100 rapid emails)
- [ ] Verify email logs are capturing all sends
- [ ] Test SMTP connection failure handling
- [ ] Verify TLS encryption is working

### **Integration Testing**

```bash
# Test with actual crisis screening
curl -X POST http://localhost:8000/api/v1/screening/phq9 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "q1_interest": 3,
    "q2_depressed": 3,
    "q3_sleep": 3,
    "q4_energy": 3,
    "q5_appetite": 3,
    "q6_self_worth": 3,
    "q7_concentration": 3,
    "q8_motor": 3,
    "q9_suicide": 2
  }'

# Should trigger crisis email
# Check logs for email send confirmation
```

---

## 📊 Monitoring & Alerts

### **Key Metrics to Monitor**

1. **Delivery Rate:** Should be >99%
2. **Bounce Rate:** Should be <1%
3. **Send Time:** Should be <30 seconds
4. **Failed Sends:** Alert immediately if >0

### **Alerting Setup**

```python
# Add to monitoring system
ALERT_IF(
    email_delivery_rate < 0.99,
    severity="CRITICAL",
    message="Crisis email delivery rate below 99%"
)

ALERT_IF(
    email_send_time > 60,
    severity="WARNING",
    message="Crisis emails taking too long to send"
)
```

---

## 🚨 Troubleshooting

### **Emails Not Sending**

1. Check SMTP credentials in `.env`
2. Verify network can reach SMTP host
3. Check provider dashboard for errors
4. Review logs: `tail -f logs/app.log | grep email`

### **Emails Going to Spam**

1. Setup SPF/DKIM/DMARC records
2. Verify sender domain
3. Check email content (avoid spam words)
4. Reduce email frequency

### **Slow Email Delivery**

1. Check network latency
2. Verify SMTP provider performance
3. Consider async email sending
4. Implement queue system

---

## 📞 Emergency Contacts

If crisis emails are NOT being delivered:

1. **Immediate:** Call on-call clinician directly
2. **Manual Check:** Log into dashboard and review alerts
3. **Fallback:** Use secondary notification system
4. **IT:** Alert engineering team immediately

---

## ✅ Final Checklist

Before going live:

- [ ] SMTP provider selected and configured
- [ ] API keys/credentials obtained
- [ ] `.env` file updated with SMTP settings
- [ ] DNS records configured (SPF, DKIM, DMARC)
- [ ] Test email sent successfully
- [ ] Crisis email templates reviewed by clinical team
- [ ] Email monitoring configured
- [ ] Alert system setup for delivery failures
- [ ] Fallback procedure documented
- [ ] On-call rotation established

---

**Remember:** Crisis emails are a LIFE-SAFETY system. They MUST work reliably.

**Questions?** Contact: engineering@psychsync.ai
