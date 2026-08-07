// src/hooks/useRoleNavigation.ts - Hook for role-based navigation

import { useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  UserRole,
  filterNavigationByRole,
  getRoleBasedSections,
  isHRUser,
  isEmployee,
  isAdmin,
  getRoleDisplayName,
  getRoleBadgeColor,
} from '../utils/roleUtils';
import type { NavigationItem } from '../utils/roleUtils';

export const useRoleNavigation = () => {
  const { user } = useAuth();

  const userRole = (user?.role || 'user') as UserRole;

  return {
    userRole,
    isHR: isHRUser(userRole),
    isEmployee: isEmployee(userRole),
    isAdmin: isAdmin(userRole),
    roleDisplayName: getRoleDisplayName(userRole),
    roleBadgeColor: getRoleBadgeColor(userRole),
    filterItems: (items: NavigationItem[]) => filterNavigationByRole(items, userRole),
    getSections: () => getRoleBasedSections(userRole),
  };
};
