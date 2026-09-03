# Role-Based Navigation System

## Overview

PsychSync now features a comprehensive role-based navigation system that shows different layouts and features based on user roles. This ensures employees see only relevant features while HR/Manager users have access to advanced analytics and management tools.

## User Roles

| Role | Description | Access Level |
|------|-------------|--------------|
| **employee** / **user** | Regular employee | Basic features, clinical tools |
| **hr** | HR Manager | All employee features + HR analytics |
| **manager** | Team Manager | All employee features + team management |
| **admin** | System Administrator | All features + system management |
| **super_admin** | Super Administrator | Full access to everything |

## Role Permissions

### 👤 Employee / User
**Can See:**
- ✅ Core Navigation (Dashboard, Icon Gallery, Teams, Settings)
- ✅ Clinical Screening (all assessments)
- ✅ Clinical Services & Resources
- ✅ Public Access pages

**Cannot See:**
- ❌ Early Warning & Risk
- ❌ Email Monitoring
- ❌ HRIS Analytics
- ❌ Services & Connectors

### 👔 HR Manager / Manager
**Can See:**
- ✅ Everything Employees can see
- ✅ Early Warning & Risk (burnout, behavioral analytics, etc.)
- ✅ Email Monitoring (email connector, sentiment analysis)
- ✅ HRIS Analytics (9 detailed analytics dashboards)
- ✅ Services & Connectors

**Cannot See:**
- ❌ System administration features

### 🛡️ Admin / Super Admin
**Can See:**
- ✅ All features across all sections
- ✅ Full system management capabilities

## Implementation Details

### Files Modified

1. **`src/utils/roleUtils.ts`** - Core role utility functions
2. **`src/hooks/useRoleNavigation.ts`** - React hook for role-based navigation
3. **`src/types/index.ts`** - Extended User interface with role field
4. **`src/components/layout/Sidebar.tsx`** - Updated sidebar with role filtering
5. **`src/components/layout/DashboardLayout.tsx`** - Role badge in user menu

### Usage Example

```typescript
import { useRoleNavigation } from '@/hooks/useRoleNavigation';

function MyComponent() {
  const { isHR, isAdmin, userRole, filterItems } = useRoleNavigation();

  // Show HR-only features
  if (isHR) {
    return <HRDashboard />;
  }

  // Filter navigation items
  const visibleItems = filterItems(allItems);

  return <EmployeeView />;
}
```

### Adding Role Requirements to Navigation Items

#### Sidebar Sections
```typescript
const mySection: MenuSection = {
  name: 'My Section',
  path: '/my-section',
  icon: '📊',
  requiredRoles: ['hr', 'admin', 'super_admin', 'manager'], // Only HR/Managers
  items: [...]
};
```

#### Individual Navigation Items
```typescript
const item: NavigationItem = {
  name: 'Admin Panel',
  path: '/admin',
  icon: '🔧',
  requiredRoles: ['admin', 'super_admin'], // Only admins
  description: 'System administration'
};
```

## Role Badge Display

### In User Dropdown Menu
The role badge appears next to the user's name in the dropdown menu:
- 🟠 **Orange** = Admin/Super Admin
- 🟣 **Purple** = HR/Manager
- 🔵 **Blue** = Employee

### In Sidebar
A small role indicator badge appears in the "Core" section header when sidebar is expanded.

## Testing Role-Based Navigation

### Method 1: Modify User Data
```javascript
// In browser console
localStorage.setItem('user', JSON.stringify({
  ...user,
  role: 'hr' // Change to 'hr', 'admin', 'manager', etc.
}));
location.reload();
```

### Method 2: Backend Integration
Ensure your backend returns the role field in the user object:

```python
# FastAPI backend example
class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: Literal['user', 'hr', 'manager', 'admin', 'super_admin']
    # ... other fields
```

## Role-Based Routing (Future Enhancement)

To protect routes at the router level, you can add a wrapper component:

```typescript
// src/components/ProtectedRoute.tsx
import { useRoleNavigation } from '@/hooks/useRoleNavigation';

export const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles: string[];
}> = ({ children, allowedRoles }) => {
  const { userRole } = useRoleNavigation();

  if (!allowedRoles.includes(userRole)) {
    return <Navigate to="/unauthorized" />;
  }

  return <>{children}</>;
};

// Usage in App.tsx
<Route path="/hris-analytics" element={
  <ProtectedRoute allowedRoles={['hr', 'admin', 'super_admin', 'manager']}>
    <HRISAnalytics />
  </ProtectedRoute>
} />
```

## Best Practices

1. **Default to Least Privilege**: Start with employee access, add permissions for higher roles
2. **Clear Role Descriptions**: Document what each role can do
3. **Consistent Role Checking**: Use the `useRoleNavigation` hook everywhere
4. **Visual Feedback**: Show role badges so users understand their access level
5. **Graceful Degradation**: Hide features gracefully without breaking the UI

## Migration Notes

### Existing Users
All existing users without a role field default to `'user'` (employee role).

### Backend Update Required
For this system to work properly, your backend needs to:
1. Store user role in the database
2. Return the role field in `/auth/me` endpoint
3. Validate role permissions for protected endpoints

### Database Migration Example
```sql
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
ALTER TABLE users ADD CONSTRAINT role_check
  CHECK (role IN ('user', 'employee', 'hr', 'manager', 'admin', 'super_admin'));

-- Set some users as HR
UPDATE users SET role = 'hr' WHERE email IN ('hr@example.com');
```

## Troubleshooting

### All Sections Hidden
**Problem**: User doesn't see any navigation sections
**Solution**: Check that user has a valid role assigned

### HR Sections Not Showing
**Problem**: HR user can't see HR-specific sections
**Solution**: Verify `user.role === 'hr'` in localStorage and user object

### Role Badge Not Displaying
**Problem**: No role badge in user menu
**Solution**: Ensure user object has `role` property set

## Future Enhancements

- [ ] Route-level protection with `<ProtectedRoute>` component
- [ ] Fine-grained permissions (e.g., `can_view_analytics`, `can_manage_users`)
- [ ] Role-based API request middleware
- [ ] Audit logging for role changes
- [ ] Team-based permissions in addition to user roles
- [ ] Custom role creation for enterprise plans
