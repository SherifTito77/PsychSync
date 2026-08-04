# ✉️ Email Actions Feature - Complete Guide

## ✅ Email Actions Implementation Complete!

Users can now **reply, forward, and compose emails** directly from the dashboard without switching to their email client.

---

## 🚀 Quick Start

### 1. Backend Setup

The backend service is already implemented:

```python
# Service: app/services/email_action_service.py
# Endpoints: app/api/v1/endpoints/email_actions.py
# API Routes: /api/v1/email-actions/*
```

### 2. Environment Configuration

Add these to your `.env` file:

```bash
# SMTP Configuration (for sending emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Frontend Integration

```tsx
// 1. Import the hook and modal
import { useEmailActions } from '@/hooks/useEmailActions';
import EmailActionsModal from '@/components/EmailActionsModal';

// 2. Use in your component
function YourComponent() {
  const { isOpen, mode, originalEmail, openReply, openForward, openCompose, close } = useEmailActions();

  return (
    <>
      <button onClick={() => openReply(emailData)}>Reply</button>
      <button onClick={() => openForward(emailData)}>Forward</button>
      <button onClick={openCompose}>Compose</button>

      <EmailActionsModal
        isOpen={isOpen}
        mode={mode}
        originalEmail={originalEmail}
        onClose={close}
      />
    </>
  );
}
```

---

## 📋 Features Overview

### ✅ Implemented Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Reply** | ✅ Complete | Reply to emails with threading support |
| **Reply All** | ✅ Complete | Reply to all recipients |
| **Forward** | ✅ Complete | Forward emails with message |
| **Compose** | ✅ Complete | Compose new emails |
| **SMTP Integration** | ✅ Complete | Sends via SMTP server |
| **Threading** | ✅ Complete | Maintains conversation threads |
| **Validation** | ✅ Complete | Email format validation |
| **Error Handling** | ✅ Complete | User-friendly error messages |
| **Loading States** | ✅ Complete | Visual feedback during sending |

---

## 🔌 API Endpoints

### Reply to Email
```http
POST /api/v1/email-actions/reply
Content-Type: application/json
Authorization: Bearer <token>

{
  "original_email": {
    "from_email": "sender@example.com",
    "subject": "Original Subject",
    "body": "Original message body",
    "message_id": "msg-12345",
    "references": "",
    "cc": ["cc@example.com"]
  },
  "reply_body": "My reply message",
  "reply_all": false
}
```

### Forward Email
```http
POST /api/v1/email-actions/forward
Content-Type: application/json
Authorization: Bearer <token>

{
  "original_email": {
    "from_email": "sender@example.com",
    "subject": "Original Subject",
    "body": "Original message",
    "date": "2026-01-22T10:00:00Z"
  },
  "forward_to": "recipient@example.com",
  "forward_message": "I thought you'd find this interesting"
}
```

### Compose New Email
```http
POST /api/v1/email-actions/compose
Content-Type: application/json
Authorization: Bearer <token>

{
  "to": "recipient@example.com",
  "subject": "New Subject",
  "body": "Email content",
  "cc": ["cc1@example.com"],
  "bcc": ["bcc1@example.com"]
}
```

---

## 🎨 Frontend Components

### 1. EmailActionsModal

**Location:** `frontend/src/components/EmailActionsModal.tsx`

**Props:**
```typescript
interface EmailActionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'reply' | 'forward' | 'compose';
  originalEmail?: {
    from_email: string;
    subject: string;
    body: string;
    message_id?: string;
    date?: string;
  };
  onSuccess?: () => void;
}
```

**Features:**
- 📝 Rich text area for composing messages
- ✉️ Email validation
- 📊 Character counter
- ⏳ Loading states
- ✅ Success/error messages
- 🎨 Responsive design
- ⌨️ Keyboard accessible

### 2. useEmailActions Hook

**Location:** `frontend/src/hooks/useEmailActions.ts`

**Returns:**
```typescript
{
  isOpen: boolean;
  mode: 'reply' | 'forward' | 'compose';
  originalEmail: OriginalEmail | null;
  openReply: (email: OriginalEmail) => void;
  openForward: (email: OriginalEmail) => void;
  openCompose: () => void;
  close: () => void;
}
```

### 3. Example Integration

**Location:** `frontend/src/components/EmailActionsExample.tsx`

Shows multiple integration patterns:
- Single action buttons
- Action dropdown menu
- Complete integration example

---

## 🔧 Backend Implementation

### EmailActionService Class

**Location:** `app/services/email_action_service.py`

**Methods:**

```python
async def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: str,
    is_html: bool = False,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    attachments: Optional[List[Dict]] = None
) -> Dict[str, Any]

async def reply_to_email(
    original_email: Dict[str, Any],
    reply_body: str,
    from_email: str,
    reply_all: bool = False
) -> Dict[str, Any]

async def forward_email(
    original_email: Dict[str, Any],
    forward_to: str,
    forward_message: str,
    from_email: str
) -> Dict[str, Any]

async def compose_new_email(
    to: str,
    subject: str,
    body: str,
    from_email: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]
```

**Features:**
- ✅ SMTP/SSL and SMTP/TLS support
- ✅ Email threading (In-Reply-To, References headers)
- ✅ HTML and plain text support
- ✅ Attachment support (base)
- ✅ Comprehensive error handling

---

## 📱 Usage Examples

### Example 1: Add Reply Button to Email List

```tsx
import { useEmailActions } from '@/hooks/useEmailActions';
import EmailActionsModal from '@/components/EmailActionsModal';

function EmailList({ emails }) {
  const { isOpen, mode, originalEmail, openReply, close } = useEmailActions();

  return (
    <>
      {emails.map(email => (
        <div key={email.id} className="email-item">
          <h4>{email.subject}</h4>
          <p>{email.snippet}</p>
          <button onClick={() => openReply(email)}>
            Reply
          </button>
        </div>
      ))}

      <EmailActionsModal
        isOpen={isOpen}
        mode={mode}
        originalEmail={originalEmail}
        onClose={close}
      />
    </>
  );
}
```

### Example 2: Compose Button in Navigation

```tsx
import { useEmailActions } from '@/hooks/useEmailActions';
import EmailActionsModal from '@/components/EmailActionsModal';

function Navigation() {
  const { isOpen, mode, originalEmail, openCompose, close } = useEmailActions();

  return (
    <>
      <nav>
        <button onClick={openCompose}>
          ✉️ Compose
        </button>
      </nav>

      <EmailActionsModal
        isOpen={isOpen}
        mode={mode}
        originalEmail={originalEmail}
        onClose={close}
      />
    </>
  );
}
```

### Example 3: Action Menu with Multiple Options

```tsx
function EmailActions({ email }) {
  const { isOpen, mode, originalEmail, openReply, openForward, close } = useEmailActions();

  return (
    <>
      <div className="dropdown">
        <button>Actions ▼</button>
        <div className="dropdown-menu">
          <button onClick={() => openReply(email)}>Reply</button>
          <button onClick={() => openForward(email)}>Forward</button>
        </div>
      </div>

      <EmailActionsModal
        isOpen={isOpen}
        mode={mode}
        originalEmail={originalEmail}
        onClose={close}
      />
    </>
  );
}
```

---

## 🔐 Security & Authentication

### User Email Resolution

The system automatically uses the authenticated user's email:

```python
# In endpoint handler
from_email = current_user.email  # From JWT token
```

### SMTP Credentials

SMTP credentials are stored securely in environment variables:

```bash
# .env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

**Gmail Users:** Generate an App Password at https://myaccount.google.com/apppasswords

---

## 📧 Email Threading

The system maintains proper email threading:

### Reply Email Headers
```
From: user@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id@example.com>
References: <original-message-id@example.com>
```

### Forward Email Format
```
My additional message

---------- Forwarded message ----------
From: original-sender@example.com
Date: Original date
Subject: Original Subject

Original email body...
```

---

## 🎯 Integration with Email Monitoring

### Add Actions to Monitoring Dashboard

```tsx
// In EmailMonitoringDashboard.tsx

import { useEmailActions } from '@/hooks/useEmailActions';
import EmailActionsModal from '@/components/EmailActionsModal';

function EmailMonitoringDashboard() {
  const [stats, setStats] = useState(null);
  const { isOpen, mode, originalEmail, openReply, openForward, openCompose, close } = useEmailActions();

  // Add action buttons to recent emails or alerts
  return (
    <div>
      {/* Your existing dashboard code */}

      {/* Add compose button */}
      <button onClick={openCompose} className="btn-compose">
        ✉️ Compose Email
      </button>

      {/* Email Actions Modal */}
      <EmailActionsModal
        isOpen={isOpen}
        mode={mode}
        originalEmail={originalEmail}
        onClose={close}
        onSuccess={() => {
          // Refresh monitoring data after sending
          fetchMonitoringStats();
        }}
      />
    </div>
  );
}
```

---

## 🚀 Advanced Features

### Custom From Email

Override the default user email:

```python
# In backend endpoint
from_email = request.from_email or current_user.email
```

### HTML Email Support

Send HTML-formatted emails:

```python
await email_action_service.send_email(
    to="recipient@example.com",
    subject="HTML Email",
    body="<h1>Hello</h1><p>This is <b>HTML</b> email</p>",
    from_email="sender@example.com",
    is_html=True
)
```

### Attachments (Base Implementation)

The attachment system is ready. To enable:

```python
attachments = [{
    'filename': 'document.pdf',
    'maintype': 'application',
    'subtype': 'pdf',
    'content': base64_encoded_content
}]

await email_action_service.send_email(
    to="recipient@example.com",
    subject="Email with attachment",
    body="Please find attached document",
    from_email="sender@example.com",
    attachments=attachments
)
```

---

## 🐛 Troubleshooting

### "SMTP authentication failed"

**Solution:**
1. Verify SMTP credentials in `.env`
2. For Gmail, use App Password (not regular password)
3. Check SMTP port (587 for TLS, 465 for SSL)

### "Email not sending"

**Solutions:**
1. Check backend logs: `/tmp/backend.log`
2. Verify SMTP server is accessible
3. Check firewall settings
4. Ensure user has valid email address

### "Modal not opening"

**Solutions:**
1. Check browser console for errors
2. Verify hook is properly initialized
3. Ensure modal is rendered in component tree

---

## 📊 Testing

### Test Email Actions

1. **Start backend:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Test API endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/email-actions/compose \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "to": "test@example.com",
       "subject": "Test Email",
       "body": "This is a test email"
     }'
   ```

3. **Test in UI:**
   - Open dashboard
   - Click "Compose" button
   - Fill form and send
   - Check recipient inbox

---

## 🎯 Roadmap

### Phase 2: Enhanced Features

- ⏳ Rich text editor (WYSIWYG)
- ⏳ File attachments with drag-and-drop
- ⏳ Email templates
- ⏳ Draft saving and auto-save
- ⏳ CC/BCC fields
- ⏳ Email scheduling (send later)
- ⏳ Read receipts
- ⏳ Signature management

### Phase 3: Advanced

- ⏳ Email threading view
- ⏳ Search sent emails
- ⏳ Undo send (5-second delay)
- ⏳ Email tracking (opens, clicks)
- ⏳ Smart compose suggestions

---

## ✨ Summary

**Status:** ✅ **COMPLETE & FUNCTIONAL**

The Email Actions feature provides:
- ✅ Reply to emails
- ✅ Forward emails
- ✅ Compose new emails
- ✅ SMTP integration
- ✅ Email threading
- ✅ Validation and error handling
- ✅ Beautiful UI with loading states
- ✅ TypeScript type safety
- ✅ Ready for production use

**Ready to integrate:** Import `useEmailActions` hook and `EmailActionsModal` component into your dashboard!

---

*Generated: 2026-01-22*
*PsychSync Email Monitoring System v1.0*
*Status: ✅ Email Actions Operational*
