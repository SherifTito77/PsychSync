# 🔧 SMTP Quick-Start Guide - Gmail (Development/Testing)

**⚠️ FOR DEVELOPMENT/TESTING ONLY - NOT HIPAA COMPLIANT FOR PRODUCTION**

---

## ⚡ 5-Minute Setup

### **Step 1: Enable 2-Factor Authentication (1 minute)**

1. Go to https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Turn it on
4. Verify your phone number

---

### **Step 2: Generate App Password (2 minutes)**

1. Stay on the security page
2. Search for "App Passwords"
3. Click "App passwords" → may need to verify password again
4. Select:
   - **Mail** for the app
   - **Other (Custom name)** → enter "PsychSync Testing"
5. Click **GENERATE**
6. **Copy the 16-character password** (it looks like: `abcd efgh ijkl mnop`)
   - **⚠️ SAVE IT NOW** - You won't see it again!

---

### **Step 3: Update .env File (1 minute)**

Edit `.env` file:

```bash
# Replace these with your actual values
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
```

**Example:**
```bash
SMTP_USER=john.doe@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
EMAILS_FROM_EMAIL=john.doe@gmail.com
```

---

### **Step 4: Test Email Delivery (1 minute)**

```bash
# Run the email test
python3 tests/test_crisis_email.py
```

**Expected Output:**
```
✅ SMTP Host: smtp.gmail.com
✅ SMTP Port: 587
✅ SMTP User: your-email@gmail.com
✅ Test email sent successfully!
   → Check your-email@gmail.com inbox (and spam folder)
```

---

## ✅ Success?

If you received the test email → **GREAT!** SMTP is working.

If you got an error:
- Check your password (common issue: spaces in password)
- Check 2-factor is enabled
- Try generating a new app password

---

## ⚠️ Before Going to Production

**Gmail is NOT HIPAA-compliant.** Before launching:

1. **Choose production SMTP provider:**
   - SendGrid (recommended): https://sendgrid.com/
   - AWS SES (cheapest): https://aws.amazon.com/ses/
   - Mailgun (good balance): https://www.mailgun.com/

2. **Update `.env` with production settings:**
   - See `CRISIS_EMAIL_SETUP_GUIDE.md` for full instructions

3. **Configure DNS records:**
   - SPF, DKIM, DMARC (your provider will give you these)

---

## 🧪 What You Can Test Now

With Gmail SMTP working, you can test:

✅ **Crisis Alerts**
```bash
# This will send actual emails!
curl -X POST http://localhost:8000/api/v1/screening/phq9 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"q1_interest":3,"q2_depressed":3,"q3_sleep":3,"q4_energy":3,"q5_appetite":3,"q6_self_worth":3,"q7_concentration":3,"q8_motor":3,"q9_suicide":2}'
```

✅ **Email Templates**
- Crisis alert emails
- Resource notification emails
- Follow-up emails

✅ **Delivery Speed**
- Check how fast emails arrive
- Verify they're not going to spam

---

## 📧 Test Email Checklist

- [ ] Test email received in inbox
- [ ] Check spam folder (mark as not spam)
- [ ] Verify email content looks correct
- [ ] Test with crisis screening (should trigger alert)
- [ ] Check delivery speed (should be < 30 seconds)

---

## 🚫 Troubleshooting

### **Error: "Invalid credentials"**
→ Regenerate app password and try again

### **Error: "Connection timeout"**
→ Check your internet connection
→ Check firewall isn't blocking port 587

### **Error: "Authentication failed"**
→ Make sure 2-factor is enabled
→ Make sure you're using app password (not regular password)

### **Emails going to spam**
→ Add sender to contacts
→ Mark as not spam
→ This is why you need production SMTP provider!

---

## 📚 Next Steps

1. ✅ Gmail working for testing
2. ⏭️ Review `CRISIS_EMAIL_SETUP_GUIDE.md`
3. ⏭️ Choose production SMTP provider
4. ⏭️ Configure production SMTP
5. ⏭️ Test with production credentials

---

**Questions?** See `CRISIS_EMAIL_SETUP_GUIDE.md` for detailed setup.

**Estimated time to complete:** 5 minutes
