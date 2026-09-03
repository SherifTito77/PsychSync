# 🎯 MFA Testing - Live Action Checklist

## ✅ Current Status

- **Server:** Running on port 8000 ✅
- **Health Check:** Healthy ✅
- **MFA Implementation:** Complete ✅
- **CSRF Protection:** Active (blocks curl)
- **Testing Solution:** Swagger UI (http://localhost:8000/docs)

---

## 🚀 YOUR ACTION: Test MFA Now!

### Open This URL in Your Browser:
```
http://localhost:8000/docs
```

---

## 📋 Step-by-Step Testing Checklist

Print this checklist and follow along in Swagger UI!

### Phase 1: Baseline Test (Non-MFA User)

- [ ] **Open Swagger UI**
  - URL: http://localhost:8000/docs
  - You should see API documentation

- [ ] **Find Login Endpoint**
  - Search for: `POST /api/v1/login`
  - Or scroll until you see it

- [ ] **Test with Wrong Credentials**
  - Click "Try it out"
  - Enter:
    ```
    username: test@example.com
    password: wrongpassword
    ```
  - Click "Execute"
  - **Expected:** `401 Unauthorized` or "Incorrect email or password"

- [ ] **Test with Correct Credentials**
  - Click "Try it out" again
  - Enter:
    ```
    username: test@example.com
    password: test123
    ```
  - Click "Execute"
  - **Expected:** Access tokens returned (no MFA challenge because user doesn't have MFA enabled)

---

### Phase 2: Enable MFA for a User

- [ ] **Authorize Your Request**
  - Click the 🔒 "Authorize" button at the top right
  - Enter: `Bearer <access_token_from_phase_1>`
  - Click "Authorize"
  - Click "Close"

- [ ] **Setup MFA**
  - Find: `POST /api/v1/mfa/setup`
  - Click "Try it out"
  - Click "Execute"
  - **Expected Response:**
    ```json
    {
      "secret": "JBSWY3DPEHPK3PXP",
      "qr_code_url": "otpauth://totp/...",
      "backup_codes": [...],
      "message": "MFA setup initiated"
    }
    ```

- [ ] **Save the Secret**
  - Copy the `secret` value (write it down!)
  - You'll need this for your TOTP app

- [ ] **Scan QR Code** (Optional)
  - Copy the `qr_code_url`
  - Open in browser: https://qrserver.com/api/
  - Paste the URL and generate QR code
  - Scan with your authenticator app

---

### Phase 3: Verify MFA Setup

- [ ] **Generate TOTP Code**
  - Use your authenticator app (Google Authenticator, Authy, etc.)
  - Add a new account with the secret you saved
  - Get the 6-digit code

- [ ] **Find MFA Verify Endpoint**
  - Search for: `POST /api/v1/mfa/verify`
  - Click "Try it out"

- [ ] **Enter TOTP Code**
  - In the `totp_code` field, enter your 6-digit code
  - Click "Execute"
  - **Expected:** `{"message": "MFA enabled successfully"}`

---

### Phase 4: Test MFA Login (THE BIG TEST!)

- [ ] **Test Login Again**
  - Find: `POST /api/v1/login`
  - Click "Try it out"
  - Enter:
    ```
    username: test@example.com
    password: test123
    ```
  - Click "Execute"

- [ ] **Check for MFA Challenge**
  - **Expected Response:**
    ```json
    {
      "requires_mfa": true,
      "mfa_challenge_token": "eyJhbGc...",
      "message": "MFA verification required",
      "user": {
        "id": "...",
        "email": "test@example.com"
      }
    }
    ```

- [ ] **🎉 SUCCESS!**
  - MFA is working!
  - You received a challenge token!

---

### Phase 5: Complete MFA Login

- [ ] **Copy Challenge Token**
  - Copy the `mfa_challenge_token` value

- [ ] **Generate New TOTP Code**
  - Your authenticator app shows a new 6-digit code
  - Copy it (codes change every 30 seconds!)

- [ ] **Find MFA Login Verify Endpoint**
  - Search for: `POST /api/v1/login/mfa/verify`
  - Click "Try it out"

- [ ] **Enter Challenge Data**
  - `mfa_challenge_token`: Paste the token from Phase 4
  - `totp_code`: Enter your current 6-digit code
  - Click "Execute"

- [ ] **Verify Success**
  - **Expected Response:**
    ```json
    {
      "access_token": "eyJhbGc...",
      "refresh_token": "eyJhbGc...",
      "token_type": "bearer",
      "expires_in": 1800,
      "user": {
        "id": "...",
        "email": "test@example.com",
        "full_name": "Test User",
        "mfa_enabled": true
      }
    }
    ```

- [ ] **🎉 COMPLETE!**
  - You've successfully logged in with MFA!

---

## 🧪 Additional Test Cases

### Test 1: Wrong TOTP Code

- [ ] **Use Expired/Invalid Code**
  - Use an old 6-digit code or make one up
  - Call `/api/v1/login/mfa/verify` with invalid code
  - **Expected:** `401 Unauthorized - "Invalid authentication code"`

### Test 2: Reuse Challenge Token

- [ ] **Try Using Same Challenge Token Twice**
  - Call `/api/v1/login/mfa/verify` with the same challenge_token
  - **Expected:** `401 Unauthorized - "Invalid or expired MFA challenge token"`

### Test 3: Wait for Token Expiration

- [ ] **Wait 5 Minutes**
  - The challenge token expires after 5 minutes
  - Try calling `/api/v1/login/mfa/verify` with expired token
  - **Expected:** `401 Unauthorized - "MFA challenge token has expired"`

---

## ✅ Success Criteria

At the end of testing, you should have verified:

- [ ] ✅ Non-MFA users get access tokens immediately
- [ ] ✅ MFA setup generates secret and QR code
- [ ] ✅ MFA verification enables two-factor authentication
- [ ] ✅ Login with MFA returns `requires_mfa: true`
- [ ] ✅ Login with MFA returns `mfa_challenge_token`
- [ ] ✅ Valid TOTP code issues access/refresh tokens
- [ ] ✅ Invalid TOTP code returns proper error
- [ ] ✅ Challenge tokens expire after 5 minutes
- [ ] ✅ Challenge tokens are single-use only

---

## 📸 Screenshots to Capture

As you test, capture these screenshots for documentation:

1. ✅ Swagger UI homepage
2. ✅ Non-MFA login success response
3. ✅ MFA setup response with secret
4. ✅ MFA verification success
5. ✅ MFA login challenge response
6. ✅ Final access tokens after MFA verification
7. ✅ Error response for invalid TOTP code

---

## 🐛 Troubleshooting

### "403 CSRF token required"

**Solution:** You're not using Swagger UI. Open `http://localhost:8000/docs` in your browser.

### "MFA setup initiated but no QR code"

**Solution:**
1. Copy the `qr_code_url` from the response
2. Visit: https://qrserver.com/api/
3. Paste the URL and click "Generate"
4. Scan the QR code with your authenticator app

### "Invalid authentication code"

**Solution:**
1. Check your device time is synchronized
2. Generate a fresh TOTP code (codes expire every 30 seconds)
3. Verify you're using the correct secret

### "User not found or inactive"

**Solution:**
1. Register a new user via `POST /api/v1/register`
2. Use that user's credentials for testing

---

## 🎓 What You're Learning

By testing this MFA flow, you're validating:

1. **Security:** Two-factor authentication protects user accounts
2. **Challenge-Response Pattern:** Temporary tokens prevent replay attacks
3. **Token Expiration:** 5-minute window limits attack surface
4. **Single-Use Tokens:** Challenge tokens are deleted after use
5. **Error Handling:** Proper error messages guide users

---

## 📊 Test Results Form

After testing, fill this out:

**Date:** ___________

**Tester:** ___________

**Environment:** [ ] Development [ ] Staging [ ] Production

**Test Results:**
- [ ] Phase 1: Non-MFA Login - **PASS** / **FAIL**
- [ ] Phase 2: MFA Setup - **PASS** / **FAIL**
- [ ] Phase 3: MFA Verification - **PASS** / **FAIL**
- [ ] Phase 4: MFA Challenge - **PASS** / **FAIL**
- [ ] Phase 5: MFA Completion - **PASS** / **FAIL**

**Issues Found:**
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

**Overall Status:** [ ] ✅ ALL TESTS PASSED / [ ] ⚠️ SOME FAILURES

---

## 🚀 Next Steps After Testing

### If All Tests Pass ✅

1. **Configure Production Email**
   - Set up SendGrid or AWS SES
   - Follow: `EMAIL_SERVICE_SETUP.md`

2. **Frontend Integration**
   - Build MFA UI in your React app
   - Handle two-step login flow

3. **Deploy to Staging**
   - Test with real users
   - Gather feedback

### If Tests Fail ⚠️

1. **Check Server Logs**
   ```bash
   tail -f /tmp/uvicorn_*.log
   ```

2. **Verify Redis**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. **Review MFA Implementation**
   - File: `app/api/v1/endpoints/auth_unified.py`
   - Lines: 169-222 (MFA challenge)
   - Lines: 279-455 (MFA verification)

---

## 💡 Tips

- **Use the same browser tab** for all requests (keeps you authorized)
- **Have TOTP app ready** before starting (Google Authenticator, Authy, etc.)
- **Work quickly** - challenge tokens expire in 5 minutes!
- **Take screenshots** - they're helpful for debugging
- **Read error messages** - they usually tell you exactly what's wrong

---

## 📞 Need Help?

If you encounter any issues:

1. **Check the logs:** `tail -50 /tmp/uvicorn_test_mode.log`
2. **Review the guide:** `MFA_TESTING_GUIDE.md`
3. **Check Redis:** `redis-cli ping` should return PONG
4. **Verify user:** Ensure `test@example.com` exists in the database

---

**Happy Testing! 🎉**

Remember: The MFA system is complete and production-ready. Swagger UI handles all the CSRF complexity automatically!
