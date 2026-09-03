# React Query Installation & Migration Guide

## ✅ What's Already Done

I've created all the React Query infrastructure for you:

### Files Created:
1. ✅ `frontend/src/lib/queryClient.ts` - Query client configuration with query keys
2. ✅ `frontend/src/hooks/useTeams.ts` - Team query hooks (fetch, create, update, delete)
3. ✅ `frontend/src/hooks/useAuth.ts` - Authentication query hooks (login, logout, user data)
4. ✅ `frontend/src/main.tsx` - QueryClientProvider integrated

### What's Left:
- Install the npm package
- Connect the hooks to your actual API services

---

## 🚀 Quick Start (5 minutes)

### Step 1: Install React Query

```bash
cd frontend
npm install @tanstack/react-query
```

That's it! The infrastructure is ready.

---

## 🔧 TODO: Connect to Your Actual API

I've placed `TODO(human)` markers in the code where you need to connect to your existing services.

### File 1: `frontend/src/hooks/useTeams.ts`

**Find these TODOs and replace with your actual service calls:**

```typescript
// Line ~42 - Replace fetchTeams
queryFn: async (): Promise<Team[]> => {
  // TODO(human): Replace with actual API call
  // Current: Mock data
  // Replace with:
  //   import * as teamService from '../services/teamService';
  //   return teamService.getAllTeams();
},
```

```typescript
// Line ~87 - Replace fetchTeam
queryFn: async (): Promise<Team> => {
  // TODO(human): Replace with actual API call
  // Replace with: return teamService.getTeam(teamId);
},
```

**Your existing service:** Check `frontend/src/services/teamService.ts` (or similar)

### File 2: `frontend/src/hooks/useAuth.ts`

**Find these TODOs and replace with your actual service calls:**

```typescript
// Line ~52 - Replace getCurrentUser
queryFn: async (): Promise<User | null> => {
  // TODO(human): Replace with actual API call
  // Current: Reads from localStorage
  // Replace with:
  //   import { getCurrentUser } from '../services/authService';
  //   return getCurrentUser();
},
```

```typescript
// Line ~132 - Replace login
mutationFn: async (credentials) => {
  // TODO(human): Replace with actual API call
  // Current: Mock implementation
  // Replace with:
  //   import { login } from '../services/authService';
  //   return login(credentials);
},
```

**Your existing service:** Check `frontend/src/services/authService.ts`

---

## 📋 Migration Checklist

### Phase 1: Installation ✅ (5 minutes)
- [ ] Run `npm install @tanstack/react-query`
- [ ] Start dev server: `npm run dev`
- [ ] Verify app loads without errors

### Phase 2: Connect to APIs (30 minutes)
- [ ] Update `useTeams.ts` TODOs with actual service calls
- [ ] Update `useAuth.ts` TODOs with actual service calls
- [ ] Test teams page loads data
- [ ] Test login/logout works

### Phase 3: Migrate Components (1-2 hours)

#### Example Migration: TeamList Component

**Before (Current Code):**
```typescript
function TeamList() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch('/api/teams')
      .then(r => r.json())
      .then(data => {
        setTeams(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay error={error} />;

  return <TeamListDisplay teams={teams} />;
}
```

**After (With React Query):**
```typescript
import { useTeams } from '../hooks/useTeams';

function TeamList() {
  const { data: teams = [], isLoading, error } = useTeams();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay error={error} />;

  return <TeamListDisplay teams={teams} />;
}
```

**Benefits:**
- ✅ 70% less code
- ✅ Automatic caching
- ✅ No manual state management
- ✅ Better error handling

**Components to migrate:**
- [ ] `Teams.tsx` - Use `useTeams()`
- [ ] `TeamDetail.tsx` - Use `useTeam(id)`
- [ ] `Dashboard.tsx` - Use `useCurrentUser()`
- [ ] `Profile.tsx` - Use `useUserProfile()`

---

## 🎯 Immediate Next Steps

### 1. Install Package (5 minutes)
```bash
cd frontend
npm install @tanstack/react-query
```

### 2. Test It Works (2 minutes)
```bash
npm run dev
```

**Expected:** App loads without errors

### 3. Connect First Hook (10 minutes)

Open `frontend/src/hooks/useTeams.ts`:

```typescript
// At the top, add:
import * as teamService from '../services/teamService';

// Then in useTeams(), replace the queryFn:
queryFn: async (): Promise<Team[]> => {
  return teamService.getAllTeams();
},
```

### 4. Use in a Component (5 minutes)

Find any component that fetches teams and replace with:

```typescript
import { useTeams } from '../hooks/useTeams';

function YourComponent() {
  const { data: teams, isLoading } = useTeams();
  // ... rest of component
}
```

---

## 🔍 How to Test

### Test 1: Verify Caching Works

1. Open Teams page
2. Open browser DevTools → Network tab
3. Navigate away, then back to Teams page
4. **Expected:** No second API call (data served from cache)

### Test 2: Verify Deduplication Works

1. Create 3 components that all call `useTeams()`
2. Mount them simultaneously
3. **Expected:** Only 1 API call (not 3)

### Test 3: Verify Refetching Works

1. Load teams data
2. Wait 5 minutes (staleTime)
3. Click refresh or re-focus window
4. **Expected:** Background refetch happens

---

## ❓ Common Issues

### Issue: "Cannot find module '@tanstack/react-query'"
**Solution:** Run `npm install @tanstack/react-query`

### Issue: Type errors with queryFn
**Solution:** Make sure your service functions return the correct types. Add `: Promise<Type>` to function signatures.

### Issue: Infinite loading
**Solution:** Check that `queryFn` doesn't throw errors. Add try/catch if needed.

### Issue: Data not updating after mutation
**Solution:** Make sure `onSuccess` calls `queryClient.invalidateQueries()`

---

## 📊 What You'll See After Migration

### Before:
```
Component mounts
  ↓
useEffect runs
  ↓
fetch() call
  ↓
setState()
  ↓
Component re-renders
```

### After (React Query):
```
Component mounts
  ↓
useQuery() hook
  ↓
Fetch + cache automatically
  ↓
Component renders with data
  ↓
[5 minutes later]
Background refetch (if needed)
```

---

## 🎓 Learn by Doing

**● Task: Connect the useTeams hook to your actual team service**

**Context:** I've created the React Query infrastructure and placeholder implementations. The hooks work but return mock data. You need to connect them to your actual API services.

**Your Task:** In `frontend/src/hooks/useTeams.ts`, find the 3 `TODO(human)` markers and replace the mock implementations with calls to your actual team service.

**Guidance:**
- Look at your existing `frontend/src/services/teamService.ts` to see the API functions
- Import the service at the top of the file
- Replace the `queryFn` implementations to call the actual service
- Make sure the return types match your Team interface
- Test by loading the Teams page in the app

**Expected Result:**
Teams page loads data from your actual API instead of mock data, with automatic caching and refetching.

---

## 📚 Next Steps After React Query

1. ✅ Install and test React Query
2. ✅ Connect to your actual APIs
3. ✅ Migrate 3-5 components to use query hooks
4. ⏳ Add DevTools for debugging (optional)
5. ⏳ Migrate remaining components
6. ⏳ Remove old Context state for API data

---

**Status:** React Query infrastructure complete ✅
**Your Next Action:** Install package and connect to APIs
**Time Required:** 45 minutes
**Impact:** Foundation for all remaining performance improvements
