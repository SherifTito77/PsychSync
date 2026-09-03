# React Query Setup Guide for PsychSync

## Overview

This guide will help you install and configure React Query (TanStack Query) for efficient server state management in the PsychSync application.

## Benefits

- ✅ **Automatic caching** - No more manual state management for API data
- ✅ **Background refetching** - Keep data fresh without manual intervention
- ✅ **Request deduplication** - Multiple components requesting the same data = one API call
- ✅ **Optimistic updates** - Improve perceived performance
- ✅ **Better error handling** - Built-in retry logic and error states

## Installation

```bash
cd frontend
npm install @tanstack/react-query
```

## Step 1: Create Query Client

Create a new file: `frontend/src/lib/queryClient.ts`

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data stays fresh for 5 minutes
      staleTime: 5 * 60 * 1000,

      // Cache data for 10 minutes
      gcTime: 10 * 60 * 1000,

      // Retry failed requests once
      retry: 1,

      // Don't refetch on window focus (can be annoying)
      refetchOnWindowFocus: false,

      // Refetch on reconnect
      refetchOnReconnect: true,
    },
  },
});
```

## Step 2: Update App.tsx

Wrap your app with `QueryClientProvider`:

```typescript
// frontend/src/App.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TeamProvider>
          <NotificationProvider>
            <ThemeContextProvider>
              <AppRoutes />
            </ThemeContextProvider>
          </NotificationProvider>
        </TeamProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

## Step 3: Migrate Example - Before & After

### BEFORE (Manual State Management)

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
  if (error) return <ErrorMessage error={error} />;

  return (
    <ul>
      {teams.map(team => <li key={team.id}>{team.name}</li>)}
    </ul>
  );
}
```

### AFTER (With React Query)

```typescript
import { useQuery } from '@tanstack/react-query';

function TeamList() {
  const {
    data: teams = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['teams'],
    queryFn: async () => {
      const response = await fetch('/api/teams');
      if (!response.ok) throw new Error('Failed to fetch teams');
      return response.json();
    },
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <ul>
      {teams.map(team => <li key={team.id}>{team.name}</li>)}
    </ul>
  );
}
```

**Benefits:**
- 70% less code
- Automatic caching
- Background refetching
- Better error handling
- No manual state management

## Step 4: Create Custom Hooks

Create reusable query hooks: `frontend/src/hooks/useTeams.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Team } from '../types';

// Query hook - fetch teams
export function useTeams() {
  return useQuery({
    queryKey: ['teams'],
    queryFn: async () => {
      const response = await fetch('/api/v1/teams');
      if (!response.ok) throw new Error('Failed to fetch teams');
      return response.json();
    },
  });
}

// Mutation hook - create team
export function useCreateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (teamData: Omit<Team, 'id'>) => {
      const response = await fetch('/api/v1/teams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(teamData),
      });
      if (!response.ok) throw new Error('Failed to create team');
      return response.json();
    },
    onSuccess: () => {
      // Invalidate and refetch teams
      queryClient.invalidateQueries({ queryKey: ['teams'] });
    },
  });
}
```

## Step 5: Migrate Auth State

Instead of storing user in Context, use React Query:

```typescript
// frontend/src/hooks/useAuth.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User } from '../types';

export function useCurrentUser() {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await fetch('/api/v1/auth/me');
      if (!response.ok) {
        // Return null if not authenticated (not an error)
        if (response.status === 401) return null;
        throw new Error('Failed to fetch user');
      }
      return response.json();
    },
    retry: false, // Don't retry auth failures
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!response.ok) throw new Error('Login failed');
      return response.json();
    },
    onSuccess: () => {
      // Refetch current user after login
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Logout failed');
      return response.json();
    },
    onSuccess: () => {
      // Clear all queries on logout
      queryClient.clear();
    },
  });
}
```

## Step 6: Update Components to Use Queries

Replace Context usage with Query hooks where appropriate:

```typescript
// BEFORE
function Dashboard() {
  const { user } = useAuth();
  const { teams } = useTeam();

  return <div>Welcome {user?.name}, you have {teams.length} teams</div>;
}

// AFTER
function Dashboard() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const { data: teams, isLoading: teamsLoading } = useTeams();

  if (userLoading || teamsLoading) return <LoadingSpinner />;

  return <div>Welcome {user?.name}, you have {teams?.length || 0} teams</div>;
}
```

## Step 7: Add DevTools (Optional)

For development, add React Query DevTools:

```bash
npm install --save-dev @tanstack/react-query-devtools
```

```typescript
// frontend/src/App.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* ... app ... */}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

## Common Patterns

### Pagination

```typescript
function useTeamsPage(page: number) {
  return useQuery({
    queryKey: ['teams', page],
    queryFn: () => fetch(`/api/teams?page=${page}`).then(r => r.json()),
  });
}
```

### Dependent Queries

```typescript
function useTeamMembers(teamId: number | undefined) {
  return useQuery({
    queryKey: ['teams', teamId, 'members'],
    queryFn: () => fetch(`/api/teams/${teamId}/members`).then(r => r.json()),
    enabled: !!teamId, // Only run when teamId exists
  });
}
```

### Optimistic Updates

```typescript
function useUpdateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ teamId, data }: { teamId: number; data: Partial<Team> }) => {
      const response = await fetch(`/api/teams/${teamId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.json();
    },
    onMutate: async ({ teamId, data }) => {
      // Cancel ongoing queries
      await queryClient.cancelQueries({ queryKey: ['teams'] });

      // Snapshot previous value
      const previousTeams = queryClient.getQueryData(['teams']);

      // Optimistically update
      queryClient.setQueryData(['teams'], (old: Team[] | undefined) =>
        old?.map(team => team.id === teamId ? { ...team, ...data } : team)
      );

      // Return context for rollback
      return { previousTeams };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      queryClient.setQueryData(['teams'], context?.previousTeams);
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['teams'] });
    },
  });
}
```

## Migration Checklist

- [ ] Install @tanstack/react-query
- [ ] Create queryClient
- [ ] Wrap App with QueryClientProvider
- [ ] Create useAuth query hooks
- [ ] Create useTeams query hooks
- [ ] Create other query hooks as needed
- [ ] Migrate 3-5 components to use queries
- [ ] Test thoroughly
- [ ] Add DevTools for debugging
- [ ] Remove old Context state for API data
- [ ] Update documentation

## Expected Results

After implementing React Query:

- ✅ **50% reduction in unnecessary re-renders**
- ✅ **70% less code** for data fetching
- ✅ **Automatic caching** - no manual state management
- ✅ **Better UX** - optimistic updates, background refetching
- ✅ **Improved performance** - request deduplication

## Troubleshooting

### Issue: Queries not refetching
**Solution:** Check `queryKey` consistency - same data should use same `queryKey`

### Issue: Infinite loops
**Solution:** Make sure `queryFn` is stable (use `useCallback` if needed)

### Issue: Stale data
**Solution:** Adjust `staleTime` or manually invalidate queries: `queryClient.invalidateQueries({ queryKey: ['teams'] })`

## Next Steps

1. Read the [official React Query docs](https://tanstack.com/query/latest)
2. Check out [React Query examples](https://tanstack.com/query/latest/docs/react/react/examples)
3. Implement DevTools for debugging
4. Gradually migrate all API calls to use React Query

---

**Estimated Implementation Time:** 4-6 hours
**Impact:** HIGH - Significant performance and code quality improvement
**Priority:** P1 - Implement within first sprint
