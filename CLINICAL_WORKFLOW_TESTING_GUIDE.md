# 🧪 Complete Clinical Workflow Testing Guide
## Input Blocking Fixes - Verification Steps

### 🌐 **Active Development Servers**
- **Frontend (Primary):** `http://localhost:5176/` ✅
- **Frontend (Secondary):** `http://localhost:5173/` ✅
- **Backend API:** `http://localhost:8000/` ✅

### 🔧 **Fixes Applied**
1. **CSS Injection:** Dynamic CSS to override input blocking
2. **Inline Styles:** Aggressive inline style properties
3. **Dual Components:** Fixed both consent and assessment forms

---

## **TEST 1: Clinical Consent Form**

### **URL:** `http://localhost:5176/clinical/consent?tool=phq9`

### **Expected Behavior:**
- ✅ **Page loads** with 6 consent sections
- ✅ **Console shows:** "DEBUG: 6 consent sections loaded"
- ✅ **Two checkboxes per section:** Test checkbox (first) + Original checkbox (second)

### **Test Steps:**

#### **1. Test Checkbox Functionality:**
1. **Open Developer Console** (F12 → Console)
2. **Click the first checkbox** in each section:
   - Should visually check/uncheck
   - Console shows: `"Test checkbox changed: [section-id] [true/false]"`

3. **Click the original checkbox** in each section:
   - Should visually check/uncheck
   - Console shows: `"Checkbox clicked: [section-id] [value]"`
   - Console shows: `"Checkbox clicked: [section-id] [new-value]"`

#### **2. Form Validation:**
1. **Check all required checkboxes** (marked with *)
2. **"Proceed to Assessment" button should become enabled**
3. **Click "Proceed to Assessment"**
4. **Should navigate to:** `http://localhost:5176/clinical/assessment/phq9/take`

---

## **TEST 2: Clinical Assessment Form**

### **URL:** `http://localhost:5176/clinical/assessment/phq9/take`

### **Expected Behavior:**
- ✅ **PHQ-9 Depression Screening loads**
- ✅ **Question 1 of 9 displayed**
- ✅ **Radio button options:** "Not at all", "Several days", "More than half the days", "Nearly every day"

### **Test Steps:**

#### **1. Radio Button Selection:**
1. **Click each radio button option:**
   - Should visually select (show filled circle)
   - Should be able to change selection
   - Click behavior feels responsive

2. **Verify CSS fixes working:**
   - Cursor changes to pointer on hover
   - Visual feedback on selection

#### **2. Question Navigation:**
1. **Select an answer for Question 1**
2. **Click "Next" button**
3. **Should advance to Question 2**
4. **Progress bar should update:** "22% Complete"
5. **Click "Previous" to go back**

#### **3. Complete Assessment:**
1. **Answer all 9 questions**
2. **Final question shows "Submit" button**
3. **Submit should work** (may show results or success message)

---

## **TEST 3: Alternative Ports (Backup)**

### **If port 5176 doesn't work:**
- **Port 5173:** `http://localhost:5173/clinical/consent?tool=phq9`
- **Port 5174:** `http://localhost:5174/clinical/consent?tool=phq9`

### **Same testing steps apply**

---

## **🐛 Troubleshooting**

### **If checkboxes/radio buttons still don't work:**

#### **Check Console for:**
- JavaScript errors
- CSS loading messages
- Network errors

#### **Verify:**
- Development servers are running
- No browser extensions blocking
- Try refreshing the page (Ctrl+F5)
- Try different browser

#### **Debug Information:**
- Console should show: "Current agreements state: {}"
- Console should show: "Current errors state: []"
- Console should show: "Setting initial agreements: [object]"

---

## **📊 Success Criteria**

### **CONSENT FORM - SUCCESS:**
- ✅ Both test and original checkboxes are clickable
- ✅ Visual feedback (check/uncheck) works
- ✅ Console logs show interaction events
- ✅ "Proceed to Assessment" button enables
- ✅ Navigation to assessment works

### **ASSESSMENT FORM - SUCCESS:**
- ✅ Radio buttons are clickable and selectable
- ✅ Can navigate between questions
- ✅ Progress indicator updates
- ✅ Can submit completed assessment

---

## **🎯 Final Verification**

Once both tests pass successfully:
1. **All form inputs are working** ✅
2. **Complete clinical workflow functions** ✅
3. **No console errors** ✅
4. **Good user experience** ✅

### **Next Steps After Success:**
- Remove debug/test checkboxes
- Clean up console.log statements
- Consider making CSS fixes permanent
- Document for production deployment

---

**Status:** 🧪 **READY FOR COMPREHENSIVE TESTING**

**Start with:** `http://localhost:5176/clinical/consent?tool=phq9`

**Report results:**
- Consent form checkbox functionality ✅/❌
- Assessment form radio button functionality ✅/❌
- Any console errors or issues ✅/❌