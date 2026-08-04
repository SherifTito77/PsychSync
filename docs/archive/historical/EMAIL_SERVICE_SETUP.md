# Email Service Configuration Guide

## Overview

PsychSync uses **FastAPI-Mail** for email delivery with comprehensive security features. The email service supports:
- Email verification for new users
- Password reset emails
- Welcome emails
- Team invitation emails
- Assessment completion notifications

## Quick Setup

### Option 1: SendGrid (Recommended for Production)

**1. Create SendGrid Account**
- Go to https://sendgrid.com/
- Sign up for a free account (100 emails/day) or paid plan

**2. Generate API Key**
- Navigate to Settings → API Keys
- Create API Key with "Mail Send" permissions
- Copy the API key

**3. Configure Environment Variables**
```bash
# .env or .env.prod
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=apikey
SMTP_PASSWORD=SG.YOUR_API_KEY_HERE
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME=PsychSync
```

**4. Test Configuration**
```bash
python -c "
from app.core.config import settings
print('SMTP Host:', settings.SMTP_HOST)
print('SMTP Port:', settings.SMTP_PORT)
print('Email From:', settings.EMAILS_FROM_EMAIL)
"
```

### Option 2: AWS SES (Recommended for High Volume)

**1. Verify Email Addresses**
- Go to AWS Console → SES → Verified Identities
- Verify your domain (DKIM, SPF, and return-path)
- Verify individual email addresses for testing

**2. Create SMTP Credentials**
- AWS Console → SES → SMTP Settings → Create SMTP Credentials
- Download credentials (username and password)
- Note the SMTP server (email-smtp.US-EAST-1.amazonaws.com)

**3. Configure Environment Variables**
```bash
# .env or .env.prod
SMTP_HOST=email-smtp.US-EAST-1.amazonaws.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=YOUR_SMTP_USERNAME
SMTP_PASSWORD=YOUR_SMTP_PASSWORD
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME=PsychSync
```

### Option 3: Gmail (Development Only)

**1. Enable App Passwords**
- Google Account → Security → 2-Step Verification
- App passwords → Generate
- Copy the 16-character password

**2. Configure Environment Variables**
```bash
# .env or .env.dev
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=PsychSync (Dev)
```

**⚠️ Warning:** Gmail is for development only! It has:
- 500 emails/day limit
- 500 recipients/day limit
- May block automated sending
- Not production-ready

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | Yes | None | SMTP server hostname |
| `SMTP_PORT` | No | 587 | SMTP port (587 for TLS, 465 for SSL) |
| `SMTP_TLS` | No | True | Use STARTTLS |
| `SMTP_USER` | Yes | None | SMTP username |
| `SMTP_PASSWORD` | Yes | None | SMTP password or API key |
| `EMAILS_FROM_EMAIL` | Yes | None | From email address |
| `EMAILS_FROM_NAME` | No | "PsychSync" | From display name |
| `FRONTEND_URL` | Yes | http://localhost:3000 | Frontend URL for verification links |

## Email Templates

Email templates are located in `app/email_templates/`:

```
app/email_templates/
├── verification.html      # Email verification
├── welcome.html             # Welcome email
├── password_reset.html      # Password reset
├── team_invitation.html     # Team invitation
└── assessment_complete.html # Assessment notification
```

## Testing Email Service

### Test Email Verification

```python
import asyncio
from app.services.email_service import EmailService

async def test_email():
    email_service = EmailService()
    result = await email_service.send_verification_email(
        email="test@example.com",
        token="test_token_123",
        name="Test User"
    )
    print(f"Email sent: {result}")

asyncio.run(test_email())
```

### Test with Real Token

```bash
# Create a test user and trigger email
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'
```

## Troubleshooting

### Issue: "Email not configured" Warning

**Symptoms:**
- Logger warning: "Email not configured. Verification email not sent"
- User registration succeeds but no email sent

**Solution:**
```bash
# Check environment variables
echo $SMTP_HOST
echo $SMTP_USER

# Verify configuration
python -c "from app.core.config import settings; print(settings.SMTP_HOST)"
```

### Issue: "Authentication failed"

**Symptoms:**
- 535 Authentication Failed
- Username/password rejected

**Solutions:**

**SendGrid:**
- Verify API key is correct
- Ensure API Key has "Mail Send" permissions
- Check if API key is disabled or expired

**AWS SES:**
- Verify SMTP credentials are correct
- Ensure you're in the SES region (us-east-1, etc.)
- Check if credentials are disabled in AWS Console

**Gmail:**
- Generate new App Password
- Enable "Less Secure Apps" (not recommended)
- Check if account is locked

### Issue: "Connection timeout"

**Symptoms:**
- SMTP connection times out
- Emails don't send after waiting

**Solutions:**
1. Check firewall settings (port 587 must be open)
2. Verify SMTP host is correct
3. Try alternate port (465 for SSL, 25 for non-secure)
4. Check DNS resolution of SMTP host

### Issue: "Email marked as spam"

**Symptoms:**
- Emails go to spam folder
- Deliverability issues

**Solutions:**
1. **Verify Domain:** Set up SPF, DKIM, and DMARC
2. **Warm Up IP:** Gradually increase sending volume
3. **Check Content:** Avoid spam trigger words
4. **Use Reply-To:** Set valid reply-to address

## Production Checklist

- [x] Email service integrated in auth endpoints
- [x] EmailService imported and activated
- [ ] SMTP credentials configured (choose SendGrid/AWS SES/Gmail)
- [ ] Environment variables set
- [ ] Test email sent successfully
- [ ] Domain verified (for AWS SES)
- [ ] SPF/DKIM records configured
- [ ] Email templates customized
- [ ] Reply-to address configured
- [ ] Bounce/Complaint tracking set up
- [ ] Rate limiting configured (SendGrid/AWS)

## Security Best Practices

### ✅ Do's

- **Use API Keys:** Never use real passwords in code
- **Environment Variables:** Store credentials in `.env` (gitignored)
- **TLS/SSL:** Always use encrypted connections
- **Rate Limiting:** Respect provider rate limits
- **Verify Recipients:** Only send to verified email addresses
- **Unsubscribe Links:** Include opt-out mechanism
- **Reply-To:** Use monitored reply-to address

### ❌ Don'ts

- **Hardcode Credentials:** Never commit SMTP passwords
- **Skip Verification:** Never skip email verification in production
- **Spam Triggers:** Avoid all caps, excessive exclamation marks
- **Buying Lists:** Never purchase email lists
- **Shared Inboxes:** Don't use shared email addresses
- **Test Lists:** Don't send to real user lists during testing

## Monitoring

### Key Metrics to Track

1. **Delivery Rate:** % of emails successfully delivered
2. **Open Rate:** % of delivered emails opened
3. **Click Rate:** % of recipients who clicked links
4. **Bounce Rate:** % of emails that bounced
5. **Complaint Rate:** % of recipients who marked spam

### Monitoring Tools

- **SendGrid:** Dashboard → Email Activity
- **AWS SES:** SES → Sending Statistics
- **Custom:** Database logging of email events

## Support

**SendGrid:** https://sendgrid.com/docs/
**AWS SES:** https://docs.aws.amazon.com/ses/
**FastAPI-Mail:** https://github.com/sabuhitech/fastapi-mail

---

*Last Updated: January 8, 2026*
*Status: Production Ready*
