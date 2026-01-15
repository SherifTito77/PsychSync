# 🧪 Manual Clinical Testing Checklist

**Purpose:** Browser-based testing of clinical screening tools
**Time Required:** 30-45 minutes
**Prerequisites:** Backend running, Frontend running

---

## 🚀 **Setup**

```bash
# Terminal 1: Start Backend
cd /Users/sheriftito/Downloads/psychsync
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend/
npm run dev

# Terminal 3: Start Test Database (if needed)
docker-compose up -d db redis
```

Verify:
- ✅ Backend: http://localhost:8000/docs loads
- ✅ Frontend: http://localhost:5173 loads
- ✅ Database: Can login to application

---

## 📋 **Test 1: PHQ-9 Depression Screening**

### **1.1 Navigate to Screening**
- [ ] Login to application
- [ ] Click "Clinical Screening" in sidebar
- [ ] Select "Depression Screening (PHQ-9)"
- [ ] Verify: Purple Brain icon displays

### **1.2 Consent Flow**
- [ ] Verify consent form appears
- [ ] Read consent language
- [ ] Verify crisis resources are visible
- [ ] Check "I agree" checkbox
- [ ] Click "Continue to Assessment"

### **1.3 Complete Assessment**
- [ ] Answer Question 1: Select "Several days"
- [ ] Verify: Progress bar updates (11%)
- [ ] Answer all 9 questions with these responses:
  ```
  Q1: Several days (1)
  Q2: Several days (1)
  Q3: More than half the days (2)
  Q4: Several days (1)
  Q5: Several days (1)
  Q6: Several days (1)
  Q7: Several days (1)
  Q8: Several days (1)
  Q9: Not at all (0)  ← Important!
  ```
- [ ] Verify: No crisis alert appears for Q9
- [ ] Verify: Progress bar reaches 100%

### **1.4 Submit & View Results**
- [ ] Click "Submit Assessment"
- [ ] Verify: Loading spinner appears
- [ ] Verify: Results display within 2 seconds
- [ ] Verify: Score shows "9" (mild depression)
- [ ] Verify: Badge shows "MILD" in green
- [ ] Verify: Risk level shows "LOW RISK"
- [ ] Verify: No crisis alert banner appears
- [ ] Verify: 3 recommendations are listed

### **1.5 Crisis Path Test**
- [ ] Start new PHQ-9 screening
- [ ] Answer all questions "Nearly every day" (3) EXCEPT:
- [ ] Answer Q9: "Nearly every day" (2+)
- [ ] Verify: Crisis resources appear below Q9
- [ ] Verify: Red "If you are in crisis" banner
- [ ] Verify: 988 hotline prominently displayed
- [ ] Complete screening
- [ ] Verify: Red "CRITICAL RISK" badge
- [ ] Verify: Crisis alert banner at top
- [ ] Verify: Phone number is clickable

**✅ Pass Criteria:** All steps complete without errors, crisis triggers work correctly

---

## 📋 **Test 2: GAD-7 Anxiety Screening**

### **2.1 Navigate & Start**
- [ ] Select "Anxiety Screening (GAD-7)"
- [ ] Verify: Blue Activity icon displays
- [ ] Complete consent

### **2.2 Complete Assessment**
- [ ] Answer questions:
  ```
  Q1: Several days (1)
  Q2: More than half the days (2)
  Q3: Several days (1)
  Q4: More than half the days (2)
  Q5: Several days (1)
  Q6: Several days (1)
  Q7: More than half the days (2)
  ```
- [ ] Submit assessment

### **2.3 Verify Results**
- [ ] Score shows "10" (moderate anxiety)
- [ ] Badge shows "MODERATE" in yellow
- [ ] Risk level shows "MODERATE RISK"
- [ ] Recommendations include therapy/relaxation techniques

**✅ Pass Criteria:** Scoring accurate, recommendations relevant

---

## 📋 **Test 3: PSS-10 Stress Screening**

### **3.1 Navigate & Start**
- [ ] Select "Stress Screening (PSS-10)"
- [ ] Verify: Indigo Waves icon displays 🌊
- [ ] Complete consent

### **3.2 Reverse-Scoring Test**
- [ ] Proceed to Question 4
- [ ] Verify: Blue alert banner appears
- [ ] Verify: Text says "This question is reverse-scored"
- [ ] Verify: Explains "Never" = high stress
- [ ] Answer all questions "Never" (0) except:
  - Q4, Q5, Q7, Q8: "Very often" (4)
- [ ] Submit assessment

### **3.3 Verify Reverse Scoring**
- [ ] Score should be "0" (all reverse-scored items = 4, which become 0)
- [ ] Severity: "Low stress"
- [ ] Verify: Reverse scoring worked correctly

### **3.4 High Stress Test**
- [ ] Start new PSS-10
- [ ] Answer all questions "Very often" (4) except:
  - Q4, Q5, Q7, Q8: "Never" (0) → reverse-scored to 4
- [ ] Submit
- [ ] Verify: Score ≥ 27
- [ ] Verify: "CRITICAL RISK" badge
- [ ] Verify: Crisis alert appears

**✅ Pass Criteria:** Reverse scoring accurate, crisis triggers at ≥27

---

## 📋 **Test 4: C-SSRS Suicide Risk**

### **4.1 Navigate & Start**
- [ ] Select "Suicide Risk (C-SSRS)"
- [ ] Verify: Red Shield icon displays
- [ ] Complete consent

### **4.2 Low Risk Test**
- [ ] Answer all questions "No" (except last: 0)
- [ ] Submit
- [ ] Verify: "LOW RISK" badge
- [ ] Verify: No crisis alert

### **4.3 High Risk Test**
- [ ] Start new C-SSRS
- [ ] Answer:
  - Wish dead: "Yes"
  - Suicidal thoughts: "Yes"
  - Intent: "Strong" (3)
  - Plan: "Yes"
  - Recent attempt: "No"
  - Lifetime attempts: "0"
- [ ] Submit
- [ ] Verify: "HIGH RISK" badge
- [ ] Verify: Crisis alert appears

### **4.4 Critical Risk Test**
- [ ] Start new C-SSRS
- [ ] Answer:
  - Wish dead: "Yes"
  - Suicidal thoughts: "Yes"
  - Intent: "Strong" (3)
  - Plan: "Yes"
  - Recent attempt: "Yes" (1)
  - Lifetime attempts: "2"
- [ ] Submit
- [ ] Verify: "CRITICAL RISK" badge
- [ ] Verify: "Recent attempt" severity
- [ ] Verify: Immediate support resources display

**✅ Pass Criteria:** Risk stratification accurate at all levels

---

## 📋 **Test 5: Clinician Dashboard**

### **5.1 Access Dashboard**
- [ ] Login as clinician user
- [ ] Navigate to "Clinician Dashboard"
- [ ] Verify: Shield icon in header
- [ ] Verify: 4 stat cards display

### **5.2 View Alerts**
- [ ] Verify: "Crisis Alerts" tab selected
- [ ] Verify: Alert list displays
- [ ] Verify: Severity badges visible
- [ ] Verify: "NEW" badge on unacknowledged alerts

### **5.3 Filter Alerts**
- [ ] Click severity dropdown
- [ ] Select "Critical Only"
- [ ] Verify: Only critical alerts show
- [ ] Select "All Severity Levels"
- [ ] Verify: All alerts show

### **5.4 Search**
- [ ] Type in search box
- [ ] Verify: Results filter by patient ID or message
- [ ] Clear search
- [ ] Verify: All alerts return

### **5.5 Alert Detail Modal**
- [ ] Click on an alert
- [ ] Verify: Modal opens
- [ ] Verify: All details display (severity, score, patient info)
- [ ] Verify: Risk flags listed
- [ ] Verify: Quick action buttons show

### **5.6 Quick Actions**
- [ ] Click "Call 988 Crisis Line"
- [ ] Verify: Phone dialer opens (or confirms on desktop)
- [ ] Click "Create Referral"
- [ ] Verify: Referral form appears
- [ ] Click "View Patient Record"
- [ ] Verify: Patient profile loads
- [ ] Click "Send Safety Plan"
- [ ] Verify: Safety plan modal appears
- [ ] Click "Send Message"
- [ ] Verify: Message composer appears
- [ ] Click "Schedule Video Call"
- [ ] Verify: Scheduling modal appears

### **5.7 Acknowledge Alert**
- [ ] Click "Acknowledge & Accept"
- [ ] Verify: Button changes to "Acknowledged"
- [ ] Verify: Success message appears
- [ ] Close modal
- [ ] Verify: Alert no longer shows "NEW" badge
- [ ] Refresh page
- [ ] Verify: Alert still shows as acknowledged

**✅ Pass Criteria:** All dashboard features functional

---

## 📋 **Test 6: Mobile Responsiveness**

### **6.1 Open DevTools**
- [ ] Open Chrome DevTools (F12)
- [ ] Click "Toggle device toolbar" (Ctrl+Shift+M)
- [ ] Select: iPhone 12 Pro (390x844)

### **6.2 Test Screening on Mobile**
- [ ] Navigate to PHQ-9 screening
- [ ] Verify: Header icon and text are readable
- [ ] Verify: Progress bar fits screen
- [ ] Verify: Question text is legible
- [ ] Verify: Response buttons are large enough to tap (min 44px height)
- [ ] Verify: No horizontal scrolling needed
- [ ] Complete 3 questions
- [ ] Verify: Navigation buttons visible
- [ ] Submit assessment
- [ ] Verify: Results display correctly

### **6.3 Test Dashboard on Mobile**
- [ ] Navigate to Clinician Dashboard
- [ ] Verify: Stat cards stack vertically
- [ ] Verify: Filter dropdown accessible
- [ ] Verify: Search box usable
- [ ] Verify: Alert cards stack vertically
- [ ] Click an alert
- [ ] Verify: Modal opens and fits screen
- [ ] Verify: Close button (X) is tappable
- [ ] Verify: Quick action buttons stack vertically

**✅ Pass Criteria:** All features usable on mobile, no layout breaks

---

## 📋 **Test 7: Accessibility**

### **7.1 Keyboard Navigation**
- [ ] Unplug mouse / use Tab key only
- [ ] Tab through consent form
- [ ] Verify: Visible focus indicator on all interactive elements
- [ ] Tab through questions
- [ ] Verify: Can select responses with Enter/Space
- [ ] Navigate to submit button
- [ ] Verify: Can activate with Enter

### **7.2 Screen Reader Test**
- [ ] Enable VoiceOver (Mac: Cmd+F5) or NVDA (Windows)
- [ ] Navigate to screening
- [ ] Verify: Question text is announced
- [ ] Verify: Response options are announced with labels
- [ ] Verify: Buttons are announced with roles
- [ ] Verify: Results are announced with severity levels

### **7.3 Color Contrast**
- [ ] Use Chrome DevTools Lighthouse
- [ ] Run accessibility audit
- [ ] Verify: All text has contrast ratio ≥ 4.5:1
- [ ] Verify: Icons have adequate contrast
- [ ] Verify: Error/alert messages are readable

**✅ Pass Criteria:** WCAG 2.1 AA compliant

---

## 📋 **Test 8: Error Handling**

### **8.1 Network Error Test**
- [ ] Start screening
- [ ] Disconnect internet (turn off WiFi)
- [ ] Complete screening and submit
- [ ] Verify: Error message appears
- [ ] Verify: Message explains connectivity issue
- [ ] Verify: "Try Again" button appears
- [ ] Reconnect internet
- [ ] Click "Try Again"
- [ ] Verify: Submission succeeds

### **8.2 Server Error Test**
- [ ] Simulate server error (use browser DevTools to block API)
- [ ] Submit screening
- [ ] Verify: User-friendly error message
- [ ] Verify: No raw stack traces exposed

### **8.3 Validation Errors**
- [ ] Start screening but don't answer all questions
- [ ] Try to submit (shouldn't be possible until complete)
- [ ] Verify: Submit button disabled until all questions answered

**✅ Pass Criteria:** Graceful error handling, no crashes

---

## 📊 **Test Results Summary**

| Test | Status | Issues Found |
|------|--------|--------------|
| PHQ-9 Depression | ⬜ Pass / ❌ Fail | |
| GAD-7 Anxiety | ⬜ Pass / ❌ Fail | |
| PSS-10 Stress | ⬜ Pass / ❌ Fail | |
| C-SSRS Suicide Risk | ⬜ Pass / ❌ Fail | |
| Clinician Dashboard | ⬜ Pass / ❌ Fail | |
| Mobile Responsiveness | ⬜ Pass / ❌ Fail | |
| Accessibility | ⬜ Pass / ❌ Fail | |
| Error Handling | ⬜ Pass / ❌ Fail | |

---

## ✅ **Final Sign-Off**

**Tester Name:** _______________
**Date:** _______________
**Browser:** _______________
**Overall Status:** ⬜ ALL PASS / ❌ ISSUES FOUND

**Notes:**
```
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________
```

**Issues to Fix:**
1. ________________________________________________________________
2. ________________________________________________________________
3. ________________________________________________________________

---

`★ Insight ─────────────────────────────────────`
**Why Manual Testing Matters**: Automated tests verify **functionality**, but manual tests verify **usability**. Can a user actually complete the screening? Is the crisis hotline **clickable**? Does the **reverse scoring** make sense to a real person? These are **qualitative assessments** automation cannot capture—yet they determine whether your system **saves lives** or frustrates users.

**The "Crisis Path" Priority**: Notice Tests 1.5, 3.4, 4.4 all test crisis scenarios. This is intentional—when someone reports **suicidal ideation** or **severe stress**, every second counts. If the crisis hotline doesn't work, if the resources don't load, if the alert doesn't trigger—**someone could die**. Test these paths **first** and **most thoroughly**.

**Mobile Testing Reality**: 60% of mental health searches happen on **mobile devices** (Pew Research). People in crisis reach for their **phone**, not a laptop. If your clinician dashboard works on desktop but breaks on mobile, clinicians **cannot respond** to urgent alerts while away from their desk. Mobile isn't a "nice-to-have"—it's **clinical necessity**.
`─────────────────────────────────────────────────`
