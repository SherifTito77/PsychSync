# 🔧 Checkbox Debug Test Plan
## Clinical Consent Form Testing

### 🌐 Access URL
**Primary Test URL:** `http://localhost:5176/clinical/consent?tool=phq9`

**Alternative URLs if 5176 doesn't work:**
- `http://localhost:5173/clinical/consent?tool=phq9`
- `http://localhost:5174/clinical/consent?tool=phq9`

### 🎯 What You Should See

#### **Consent Form Layout:**
- Title: "Informed Consent"
- 6 consent sections (DEBUG: "6 consent sections loaded" message)
- Each section has **TWO checkboxes** (for testing)

#### **Checkbox Structure:**
For each consent section, you'll see:
1. **Test Checkbox** (first one) - Simple, uncontrolled, should definitely work
2. **Original Checkbox** (second one) - The one with the issue

### 🔍 Step-by-Step Testing

#### **Step 1: Test Checkbox Functionality**
1. **Open Developer Console** (F12 → Console tab)
2. **Try the Test Checkbox** (first checkbox in each section):
   - Click to check/uncheck
   - Console should show: `"Test checkbox changed: [section-id] [true/false]"`
   - You should visually see it check/uncheck

3. **Try the Original Checkbox** (second checkbox):
   - Click to check/uncheck
   - Console should show:
     - `"Checkbox click event: [section-id] [before-value]"`
     - `"Checkbox clicked: [section-id] [new-value]"`
   - Look for any console errors

#### **Step 2: Check Console Logs**
The console should show:
- `"Current agreements state: {}"` (initial state)
- `"Current errors state: []"` (initial errors)
- `"Setting initial agreements: {object}"` (initialization)
- `"Initializing agreements for tool: phq9"`

#### **Step 3: Test Different Scenarios**

**Scenario A: Test Checkbox Works, Original Doesn't**
- **Problem:** React state management issue
- **Solution:** Will fix the `agreements` state handling

**Scenario B: Neither Checkbox Works**
- **Problem:** CSS overlay, z-index, or layout issue
- **Solution:** Will fix CSS or HTML structure

**Scenario C: Both Work**
- **Problem:** May be with form validation or submit logic
- **Solution:** Will check the "Proceed" button logic

### 📊 Expected Results

#### **If Test Checkbox Works:**
```
✅ Test checkbox: Can check/uncheck
✅ Console: Shows "Test checkbox changed" messages
❓ Original checkbox: Unknown (this is what we're testing)
```

#### **If Original Checkbox Works:**
```
✅ Original checkbox: Can check/uncheck
✅ Console: Shows "Checkbox clicked" messages
✅ State: Agreements object updates in console
✅ Button: "Proceed to Assessment" becomes enabled when all required boxes checked
```

### 🐛 Common Issues to Look For

1. **Console Errors:**
   - React hydratation errors
   - JavaScript errors
   - CORS or network errors

2. **Visual Issues:**
   - Checkboxes not appearing clickable
   - Wrong cursor style
   - Overlay elements blocking clicks

3. **State Issues:**
   - Agreements state not updating
   - Validation logic not working

### 📋 Report Results

Please report:
1. **Which checkboxes work** (test vs original)
2. **Console messages** you see
3. **Any error messages** in console
4. **Visual behavior** of the checkboxes
5. **Button status** - does "Proceed to Assessment" become enabled?

### 🎯 Success Criteria

**Full Success:**
- ✅ Both test and original checkboxes work
- ✅ Console logs show state changes
- ✅ "Proceed to Assessment" button enables when all required boxes checked
- ✅ Can navigate to assessment after consenting

**Partial Success:**
- ✅ Test checkbox works (identifies the problem area)
- ❓ Original checkbox issue identified

**Next Steps Based on Results:**
- If test works but original doesn't → Fix React state management
- If neither works → Fix CSS/HTML layout issues
- If both work → Fix form validation logic

---

**Ready to test! Go to:** `http://localhost:5176/clinical/consent?tool=phq9`
