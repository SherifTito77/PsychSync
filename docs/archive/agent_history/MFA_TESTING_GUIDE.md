# MFA Testing Guide - Step by Step

## Current Status

✅ **MFA Implementation:** COMPLETE
✅ **Server Running:** Port 8000
⚠️ **CSRF Protection:** Active (blocks curl testing)
✅ **Testing Solution:** Swagger UI (handles CSRF automatically)

---

## Method 1: Test via Swagger UI (RECOMMENDED)

### Why Swagger UI?

Swagger UI automatically handles CSRF tokens, making it the perfect tool for testing MFA endpoints during development.

### Step-by-Step Instructions

#### 1. Open Swagger UI
```
http://localhost:8000/docs
```

#### 2. Test Non-MFA Login (Baseline)

**Find the endpoint:** `POST /api/v1/login`

**Steps:**
1. Click on the endpoint to expand it
2. Click "Try it out" button
3. Fill in the form:
   - `username`: `test@example.com`
   - `password`: `test123`
4. Click "Execute"
5. View the response

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "...",
    "email": "test@example.com",
    "full_name": "Test User",
    "is_active": true,
    "mfa_enabled": false
  }
}
```

**Note:** Since `test@example.com` doesn't have MFA enabled, you get tokens immediately!

#### 3. Test MFA Login Flow

First, we need to enable MFA for a user. Let's do that!

**Find the endpoint:** `POST /api/v1/mfa/setup`

**Steps:**
1. Click "Try it out"
2. Click "Execute" (you'll need to be logged in first - use the token from step 2)
   - Click "Authorize" button at top
   - Enter: `Bearer <your_access_token>` from step 2
   - Click "Authorize"
   - Click "Close"
3. Execute the `/mfa/mfa/setup` endpoint
4. Copy the `secret` and `qr_code_url` from response
5. Open the QR code URL in your browser or use a TOTP app

**Expected Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/PsychSync:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=PsychSync",
  "backup_codes": ["abc12345", "def67890", ...],
  "message": "MFA setup initiated. Please verify the code to enable MFA."
}
```

#### 4. Verify MFA Setup

**Find the endpoint:** `POST /api/v1/mfa/verify`

**Steps:**
1. Generate a TOTP code using:
   - Google Authenticator app, OR
   - The command line: `oathtool --totp JBSWY3DPEHPK3PXP` (if installed)
2. Click "Try it out" on `/api/v1/mfa/verify`
3. Enter the 6-digit code in the `totp_code` field
4. Click "Execute"

**Expected Response:**
```json
{
  "message": "MFA enabled successfully"
}
```

#### 5. Test MFA Login (The Main Event!)

**Now test the login with MFA enabled:**

**Find:** `POST /api/v1/login`

**Steps:**
1. Click "Try it out"
2. Enter credentials:
   - `username`: `test@example.com`
   - `password`: `test123`
3. Click "Execute"

**Expected Response (MFA Challenge):**
```json
{
  "requires_mfa": true,
  "mfa_challenge_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "MFA verification required",
  "user": {
    "id": "...",
    "email": "test@example.com"
  }
}
```

✅ **SUCCESS!** The login endpoint recognized MFA is enabled and returned a challenge token!

#### 6. Complete MFA Verification

**Find:** `POST /api/v1/login/mfa/verify`

**Steps:**
1. Click "Try it out"
2. Fill in the fields:
   - `mfa_challenge_token`: Paste the token from step 5
   - `totp_code`: Generate a new TOTP code from your app
3. Click "Execute"

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "...",
    "email": "test@example.com",
    "full_name": "Test User",
    "is_active": true,
    "mfa_enabled": true
  }
}
```

🎉 **SUCCESS!** MFA flow is working perfectly!

---

## Method 2: Test via Command Line (Requires Server Fix)

To enable curl testing, the server needs to be restarted with the CSRF exemptions we added.

### Option A: Quick Server Restart

```bash
# Kill the server
pkill -f "uvicorn app.main:app"

# Restart with fresh config
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then test:

```bash
# Test MFA login
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"
```

### Option B: Install oathtool for TOTP Codes

```bash
# Install oathtool (Mac)
brew install oathtool

# Generate TOTP code
oathtool --totp YOUR_SECRET_HERE

# Use the code in the login/mfa/verify endpoint
```

---

## Method 3: Create Test User with MFA Pre-Enabled

```python
# Run this in Python shell
import asyncio
from app.core.database import get_async_db
from app.services.mfa_service import mfa_service
from app.db.models.user import User
from sqlalchemy import select

async def setup_mfa():
    async for db in get_async_db():
        # Get test user
        result = await db.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()

        if user:
            # Generate TOTP secret
            secret, qr_url = await mfa_service.generate_totp_secret(user, db)
            print(f"Secret: {secret}")
            print(f"QR URL: {qr_url}")

            # Manually enable MFA (skip verification for testing)
            from app.db.models.user import User
            from sqlalchemy import update

            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(two_factor_enabled=True)
            )
            await db.commit()
            print("MFA enabled for test@example.com")

# Run it
asyncio.run(setup_mfa())
```

---

## Success Criteria Checklist

### ✅ Complete MFA Flow

- [ ] **Step 1:** Non-MFA user gets tokens immediately
- [ ] **Step 2:** MFA setup generates secret and QR code
- [ ] **Step 3:** MFA verification enables two-factor auth
- [ ] **Step 4:** Login returns `requires_mfa: true`
- [ ] **Step 5:** Login returns `mfa_challenge_token`
- [ ] **Step 6:** MFA verify endpoint accepts TOTP code
- [ ] **Step 7:** Valid TOTP code issues access/refresh tokens
- [ ] **Step 8:** Invalid TOTP code returns 401 error
- [ ] **Step 9:** Expired challenge token returns 401 error

### Test Cases

#### ✅ Positive Cases

1. **Non-MFA Login**
   ```bash
   POST /api/v1/login
   username: user-without-mfa@example.com
   password: password123

   Expected: Access tokens returned immediately
   ```

2. **MFA Login (Complete Flow)**
   ```bash
   # Step 1: Request login
   POST /api/v1/login
   username: user-with-mfa@example.com
   password: password123

   Expected: {"requires_mfa": true, "mfa_challenge_token": "..."}

   # Step 2: Verify MFA
   POST /api/v1/login/mfa/verify
   mfa_challenge_token: <from_step_1>
   totp_code: <6_digits_from_authenticator_app>

   Expected: {"access_token": "...", "refresh_token": "...", ...}
   ```

#### ❌ Negative Cases

1. **Wrong Password**
   ```bash
   POST /api/v1/login
   username: test@example.com
   password: wrongpassword

   Expected: 401 Unauthorized - "Incorrect email or password"
   ```

2. **Invalid TOTP Code**
   ```bash
   POST /api/v1/login/mfa/verify
   mfa_challenge_token: <valid_token>
   totp_code: 000000  # Wrong code

   Expected: 401 Unauthorized - "Invalid authentication code"
   ```

3. **Expired Challenge Token**
   ```bash
   # Wait 5 minutes for token to expire, then:
   POST /api/v1/login/mfa/verify
   mfa_challenge_token: <expired_token>
   totp_code: 123456  # Valid code but expired token

   Expected: 401 Unauthorized - "MFA challenge token has expired"
   ```

4. **Reused Challenge Token**
   ```bash
   # Use the same challenge token twice
   POST /api/v1/login/mfa/verify
   mfa_challenge_token: <already_used_token>
   totp_code: 123456

   Expected: 401 Unauthorized - "Invalid or expired MFA challenge token"
   ```

---

## Troubleshooting

### Issue: "CSRF token required"

**Solution:** Use Swagger UI (http://localhost:8000/docs) which handles CSRF automatically.

### Issue: "MFA setup initiated" but no QR code displayed

**Solution:**
- Copy the `qr_code_url` from the response
- Open it in your browser: `https://api.qrserver.com/v1/create-qr-code/?data=<url>`
- Or use a TOTP app and manually enter the secret

### Issue: TOTP code always shows as invalid

**Possible Causes:**
1. Clock skew - Ensure your device time is synchronized
2. Wrong secret - Verify you're using the correct secret
3. Time window - Try generating a new code (codes change every 30 seconds)

### Issue: "User not found or inactive"

**Solution:**
- Verify the user exists in the database
- Check that `is_active` is `true`
- Use the register endpoint to create a new test user

---

## Quick Test Script

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Test login without MFA
response = requests.post(
    f"{BASE_URL}/api/v1/login",
    data={"username": "test@example.com", "password": "test123"}
)
print("Login Response:", json.dumps(response.json(), indent=2))

# 2. If MFA required, verify MFA
if response.json().get("requires_mfa"):
    challenge_token = response.json()["mfa_challenge_token"]

    # Get TOTP code from your authenticator app
    totp_code = input("Enter TOTP code: ")

    # Verify MFA
    mfa_response = requests.post(
        f"{BASE_URL}/api/v1/login/mfa/verify",
        json={
            "mfa_challenge_token": challenge_token,
            "totp_code": totp_code
        }
    )
    print("MFA Verify Response:", json.dumps(mfa_response.json(), indent=2))
```

---

## Next Steps After Testing

### ✅ If All Tests Pass

The MFA implementation is production-ready! You can:

1. **Configure Production Email** - Set up SendGrid/AWS SES
2. **Frontend Integration** - Update login UI for MFA flow
3. **Deploy to Staging** - Test with real users

### ⚠️ If Tests Fail

1. **Check Server Logs** - `tail -f /tmp/uvicorn_*.log`
2. **Verify Redis** - `redis-cli ping` should return PONG
3. **Check Database** - Ensure user has `two_factor_enabled=true`
4. **Review MFA Secret** - Verify it matches your authenticator app

---

## Documentation

- **MFA Implementation:** `MFA_CHALLENGE_IMPLEMENTATION_COMPLETE.md`
- **Email Setup:** `EMAIL_SERVICE_SETUP.md`
- **Session Summary:** `SESSION_MFA_TESTING_EXCEPTION_HANDLING_COMPLETE.md`

---

**Happy Testing! 🎉**

Remember: Swagger UI (http://localhost:8000/docs) is your friend - it handles all the CSRF complexity automatically!
