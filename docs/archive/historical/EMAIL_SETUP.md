# Email Setup Guide

## Gmail Setup (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Google Account:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "PsychSync"
   - Copy the 16-character password

3. **Update `.env` file**:
```env
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   MAIL_FROM=noreply@psychsync.com
```

## Other Email Providers

### SendGrid
```env
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
MAIL_FROM=noreply@yourdomain.com
MAIL_PORT=587
MAIL_SERVER=smtp.sendgrid.net
```

### Mailgun
```env
MAIL_USERNAME=postmaster@your-domain.mailgun.org
MAIL_PASSWORD=your-mailgun-password
MAIL_FROM=noreply@yourdomain.com
MAIL_PORT=587
MAIL_SERVER=smtp.mailgun.org
```

### AWS SES
```env
MAIL_USERNAME=your-aws-smtp-username
MAIL_PASSWORD=your-aws-smtp-password
MAIL_FROM=noreply@yourdomain.com
MAIL_PORT=587
MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
```

## Testing Email in Development

For development without real email, use **Mailtrap**:

1. Sign up at https://mailtrap.io
2. Get SMTP credentials from your inbox
3. Update `.env`:
```env
   MAIL_USERNAME=your-mailtrap-username
   MAIL_PASSWORD=your-mailtrap-password
   MAIL_PORT=2525
   MAIL_SERVER=smtp.mailtrap.io
```

All emails will be caught by Mailtrap instead of being sent to real addresses.
