# Quick Setup Wizard - Implementation Guide

## ✅ Component Created!

The Quick Setup Wizard is a multi-step onboarding flow for new users. It guides users through account setup in about 2 minutes.

---

## 📁 Files Created

1. **`src/components/onboarding/QuickSetupWizard.tsx`** - Main wizard component
2. **`src/components/onboarding/SetupWizardWrapper.tsx`** - Auto-trigger wrapper

---

## 🎯 Features

### 6-Step Wizard Flow:

1. **Welcome** 🎉
   - Friendly introduction
   - Overview of what to expect
   - Time estimate (2 minutes)

2. **Profile Setup** 👤
   - Display name
   - Job title
   - Department selection
   - All optional

3. **Team Setup** 👥
   - Create new team
   - Join existing team (with code)
   - Skip for now

4. **Quick Assessment** 🧠
   - Offer to take personality assessment
   - Can skip and do later
   - ~10 minutes if taken

5. **Preferences** ⚙️
   - Email notifications toggle
   - Helpful tips

6. **Complete** 🚀
   - Success message with user's name
   - Action cards for next steps
   - Direct link to dashboard

### UI Features:
- ✅ Progress bar with percentage
- ✅ Step indicators (dots)
- ✅ Back/Next/Skip navigation
- ✅ Validation with error messages
- ✅ Loading states
- ✅ Mobile-responsive design
- ✅ Smooth animations
- ✅ Beautiful gradient background
- ✅ Skip optional steps

---

## 🔧 Integration

### Option 1: Add as a Route

Add to your `App.tsx`:

```tsx
import SetupWizardWrapper from './components/onboarding/SetupWizardWrapper';
import QuickSetupWizard from './components/onboarding/QuickSetupWizard';

function App() {
  return (
    <Routes>
      {/* Existing routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Setup Wizard Route */}
      <Route
        path="/setup-wizard"
        element={
          <RequireAuth>
            <QuickSetupWizard />
          </RequireAuth>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <DashboardLayout>
              <Dashboard />
            </DashboardLayout>
          </RequireAuth>
        }
      />

      {/* Auto-trigger wrapper - Add this to catch new users */}
      {/* See Option 2 below */}
    </Routes>
  );
}
```

### Option 2: Auto-Trigger for New Users (Recommended)

Add the wrapper to your main layout or auth flow:

```tsx
// In App.tsx or a root component
import SetupWizardWrapper from './components/onboarding/SetupWizardWrapper';

function App() {
  return (
    <>
      {/* This will automatically show wizard for new users */}
      <SetupWizardWrapper />

      <Routes>
        {/* Your existing routes */}
      </Routes>
    </>
  );
}
```

**How it works:**
- Checks if `setupWizardCompleted` exists in localStorage
- If user was created < 24 hours ago → Show wizard
- If wizard completed > 30 days ago → Optionally show again
- Skips auth pages (login, register, verify-email)

### Option 3: Trigger After Registration

In your registration success handler:

```tsx
// After successful registration
const handleRegisterSuccess = async (data) => {
  // Save user data
  localStorage.setItem('user', JSON.stringify(data.user));

  // Navigate to setup wizard instead of dashboard
  navigate('/setup-wizard');
};
```

---

## 🧪 Testing the Wizard

### Method 1: Create New User

1. Register a new account
2. After registration, you'll be redirected to the wizard automatically

### Method 2: Force Wizard for Existing User

In browser DevTools Console:

```javascript
// Mark wizard as not completed
localStorage.removeItem('setupWizardCompleted');
localStorage.removeItem('setupWizardDate');

// Or trick the system by setting a recent created_at
const user = JSON.parse(localStorage.getItem('user'));
user.created_at = new Date().toISOString();
localStorage.setItem('user', JSON.stringify(user));

// Reload the page
location.reload();
```

### Method 3: Direct Route

Simply navigate to:
```
http://localhost:5173/setup-wizard
```

---

## 🎨 Customization

### Change Steps

Edit `QuickSetupWizard.tsx`:

```tsx
const steps: WizardStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to PsychSync!', // Change title
    description: 'Let\'s get you set up',
    icon: '🎉', // Change emoji
    required: true,
  },
  // Add or remove steps here
];
```

### Add New Step

```tsx
// 1. Add to steps array
{
  id: 'custom-step',
  title: 'My Custom Step',
  description: 'Do something cool',
  icon: '✨',
  required: false,
}

// 2. Add render function
const renderCustomStep = () => (
  <div className="py-8">
    <h3>My Custom Step</h3>
    {/* Your content */}
  </div>
);

// 3. Add to renderStep() switch
case 5: return renderCustomStep();
```

### Change Colors

Edit the gradient background:

```tsx
// In QuickSetupWizard.tsx line ~570
<div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
  {/* Change colors: from-blue-50 via-white to-green-50 */}
</div>
```

---

## 📊 Data Collected

The wizard collects this data (stored in `SetupData` interface):

```typescript
{
  displayName: string;      // User's preferred name
  jobTitle: string;         // Optional job title
  department: string;       // Selected department
  teamChoice: 'create' | 'join' | 'skip';
  teamName?: string;        // If creating team
  teamCode?: string;        // If joining team
  takeAssessment: boolean;  // Wants to take assessment now
  notifications: boolean;   // Email preferences
}
```

**Note:** Currently this data is stored in component state. To persist it, you'll want to save it to your backend when the wizard completes (see `handleComplete` function).

---

## 🔌 Backend Integration (Optional)

To save the wizard data to your backend, update the `handleComplete` function:

```typescript
const handleComplete = async () => {
  setIsLoading(true);
  try {
    // Save setup data to backend
    await api.post('/api/v1/users/setup-wizard', {
      display_name: setupData.displayName,
      job_title: setupData.jobTitle,
      department: setupData.department,
      notifications_enabled: setupData.notifications,
    });

    // Mark wizard as completed
    localStorage.setItem('setupWizardCompleted', 'true');
    localStorage.setItem('setupWizardDate', new Date().toISOString());

    // If user wants to take assessment
    if (setupData.takeAssessment) {
      navigate('/assessments');
    } else {
      navigate('/dashboard');
    }
  } catch (err) {
    setError('Failed to save your preferences');
    setIsLoading(false);
  }
};
```

Backend endpoint example (FastAPI):

```python
@router.post("/users/setup-wizard")
async def complete_setup_wizard(
    data: SetupWizardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update user with setup data
    current_user.job_title = data.job_title
    current_user.department = data.department
    # ... save to database
    return {"success": True}
```

---

## 🎯 Best Practices

### 1. **Keep it Short**
- ✅ 2-3 minutes max
- ✅ 3-6 steps total
- ✅ Allow skipping optional steps

### 2. **Clear Progress**
- ✅ Show progress bar
- ✅ Display step numbers
- ✅ Indicate which steps are required

### 3. **Mobile Friendly**
- ✅ Large touch targets (44px+)
- ✅ Responsive layout
- ✅ Readable on small screens

### 4. **Error Handling**
- ✅ Validate before proceeding
- ✅ Show clear error messages
- ✅ Don't lose user's progress

### 5. **Graceful Degradation**
- ✅ Allow users to skip
- ✅ Don't block access to app
- ✅ Can return to wizard later

---

## 🚀 Launch Checklist

- [x] Wizard component created
- [x] Wrapper component created
- [x] Mobile responsive
- [x] Validation included
- [ ] Add to App.tsx routing
- [ ] Test with new user registration
- [ ] Test with existing user
- [ ] Test on mobile devices
- [ ] Add backend endpoint to save data (optional)
- [ ] Add analytics tracking (optional)

---

## 💡 Tips

1. **Test the full flow**: Register → See wizard → Complete → Dashboard
2. **Test skip functionality**: Can users skip and still use the app?
3. **Test validation**: Try to proceed without required fields
4. **Test mobile**: Check on phone for responsive issues
5. **Track completion**: Monitor how many users complete the wizard

---

## 📱 Mobile Considerations

The wizard is already mobile-optimized with:
- Touch-friendly buttons (44px+ height)
- Single column layout on small screens
- Readable text sizes
- Proper spacing between elements

---

## 🎨 Screenshot Opportunities

The wizard creates perfect screenshot opportunities:
- Welcome screen for marketing
- Progress completion for demos
- Step highlights for tutorials

---

## ✨ Summary

**Total Files:** 2
**Lines of Code:** ~600
**Features:** 6 steps, validation, progress tracking, mobile-responsive

Your Quick Setup Wizard is ready to integrate! Just add the routing or wrapper component and start onboarding new users like a pro! 🚀
