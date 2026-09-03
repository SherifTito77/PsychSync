// src/utils/roleUtils.ts - Role-based navigation utilities

export type UserRole = 'user' | 'admin' | 'super_admin' | 'hr' | 'employee' | 'manager' | 'clinician' | 'patient';

export interface NavigationItem {
  name: string;
  path: string;
  icon: string;
  description?: string;
  requiredRoles?: UserRole[];
  allowedRoles?: UserRole[];
}

/**
 * Check if user has required role
 */
export const hasRole = (userRole: UserRole | undefined, requiredRoles: UserRole[]): boolean => {
  if (!userRole) return false;
  return requiredRoles.includes(userRole);
};

/**
 * Check if user is HR or higher (admin, super_admin)
 */
export const isHRUser = (userRole: UserRole | undefined): boolean => {
  if (!userRole) return false;
  return ['hr', 'admin', 'super_admin', 'manager', 'clinician'].includes(userRole);
};

/**
 * Check if user is employee (regular user)
 */
export const isEmployee = (userRole: UserRole | undefined): boolean => {
  if (!userRole) return false;
  return userRole === 'user' || userRole === 'employee' || userRole === 'patient';
};

/**
 * Check if user is admin or super_admin
 */
export const isAdmin = (userRole: UserRole | undefined): boolean => {
  if (!userRole) return false;
  return ['admin', 'super_admin'].includes(userRole);
};

/**
 * Check if user is clinician
 */
export const isClinician = (userRole: UserRole | undefined): boolean => {
  if (!userRole) return false;
  return userRole === 'clinician' || userRole === 'super_admin' || userRole === 'admin';
};

/**
 * Filter navigation items by user role
 */
export const filterNavigationByRole = (
  items: NavigationItem[],
  userRole: UserRole | undefined
): NavigationItem[] => {
  return items.filter(item => {
    // If no roles specified, show to everyone
    if (!item.requiredRoles && !item.allowedRoles) return true;

    // If requiredRoles specified, user must have one of them
    if (item.requiredRoles && item.requiredRoles.length > 0) {
      return hasRole(userRole, item.requiredRoles);
    }

    // If allowedRoles specified, check if user's role is in the list
    if (item.allowedRoles && item.allowedRoles.length > 0) {
      return hasRole(userRole, item.allowedRoles);
    }

    return true;
  });
};

/**
 * Get role-based navigation sections
 */
export const getRoleBasedSections = (
  userRole: UserRole | undefined
): string[] => {
  const allSections = ['Core', 'Early Warning & Risk', 'Clinical Screening', 'Email Monitoring', 'HRIS Analytics', 'Clinical Services', 'Services & Connectors', 'Analytics & AI', 'Public Access'];

  if (isAdmin(userRole)) {
    // Admins see everything
    return allSections;
  }

  if (userRole === 'clinician') {
    return ['Core', 'Clinical Screening', 'Clinical Services', 'Analytics & AI'];
  }

  if (isHRUser(userRole)) {
    // HR sees everything except some admin-only sections
    return ['Core', 'Early Warning & Risk', 'Clinical Screening', 'Email Monitoring', 'HRIS Analytics', 'Clinical Services', 'Services & Connectors', 'Analytics & AI'];
  }

  if (isEmployee(userRole)) {
    // Employees see limited sections
    return ['Core', 'Clinical Screening', 'Clinical Services'];
  }

  // Default - show basic sections
  return ['Core', 'Clinical Screening', 'Public Access'];
};

/**
 * Get role display name
 */
export const getRoleDisplayName = (role: UserRole): string => {
  const roleNames: Record<UserRole, string> = {
    user: 'Employee',
    employee: 'Employee',
    patient: 'Patient',
    clinician: 'Clinician',
    hr: 'HR Manager',
    manager: 'Manager',
    admin: 'Administrator',
    super_admin: 'Super Admin'
  };
  return roleNames[role] || role;
};

/**
 * Get role badge color
 */
export const getRoleBadgeColor = (role: UserRole): string => {
  const colors: Record<UserRole, string> = {
    user: 'bg-blue-100 text-blue-700',
    employee: 'bg-blue-100 text-blue-700',
    patient: 'bg-green-100 text-green-700',
    clinician: 'bg-indigo-100 text-indigo-700',
    hr: 'bg-purple-100 text-purple-700',
    manager: 'bg-green-100 text-green-700',
    admin: 'bg-orange-100 text-orange-700',
    super_admin: 'bg-red-100 text-red-700'
  };
  return colors[role] || 'bg-gray-100 text-gray-700';
};
