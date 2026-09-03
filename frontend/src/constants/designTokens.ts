/**
 * Design Token Constants for React Native
 *
 * React Native requires numeric values for spacing and font sizes,
 * and string values for colors. This file provides type-safe access
 * to design system tokens for React Native components.
 *
 * @see frontend/src/utils/designTokens.ts for web version
 * @see frontend/src/styles/global/variables.css for CSS variables
 */

export const DESIGN_TOKENS = {
  // =========================================================================
  // COLORS
  // =========================================================================

  colors: {
    // Primary colors
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },

    // Semantic colors
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',

    // Gray scale
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },

    // Clinical colors
    clinical: {
      crisis: '#dc2626',
      high: '#f97316',
      moderate: '#f59e0b',
      low: '#10b981',
      stable: '#10b981',
    },

    // Gamification tier colors
    tier: {
      bronze: '#CD7F32',
      silver: '#C0C0C0',
      gold: '#FFD700',
      platinum: '#E5E4E2',
      diamond: '#B9F2FF',
    },

    // Platform-specific colors
    ios: {
      blue: '#007aff',
      systemGray: '#8e8e93',
    },

    android: {
      green: '#4caf50',
      purple: '#9c27b0',
    },
  },

  // =========================================================================
  // SPACING (4px base unit)
  // =========================================================================

  spacing: {
    xs: 4,    // 4px
    sm: 8,    // 8px
    md: 16,   // 16px
    lg: 24,   // 24px
    xl: 32,   // 32px
    '2xl': 48,  // 48px
    '3xl': 64,  // 64px
    '4xl': 96,  // 96px
    '5xl': 20,  // 20px (custom gap filler)
  },

  // =========================================================================
  // TYPOGRAPHY
  // =========================================================================

  typography: {
    size: {
      xs: 12,   // 12px
      sm: 14,   // 14px
      base: 16, // 16px
      lg: 18,   // 18px
      xl: 20,   // 20px
      '2xl': 24,  // 24px
      '3xl': 30,  // 30px
      '4xl': 36,  // 36px
    },

    weight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },

    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  // =========================================================================
  // BORDER RADIUS
  // =========================================================================

  radius: {
    sm: 4,    // 4px
    md: 8,    // 8px
    lg: 12,   // 12px
    xl: 16,   // 16px
    '2xl': 24,  // 24px
    full: 9999, // Pill shape
  },

  // =========================================================================
  // SHADOWS (iOS/Android platform differences handled by StyleSheet)
  // =========================================================================

  shadow: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 1, // Android
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 6,
      elevation: 4, // Android
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 10 },
      shadowOpacity: 0.15,
      shadowRadius: 15,
      elevation: 8, // Android
    },
  },

  // =========================================================================
  // Z-INDEX LAYERS
  // =========================================================================

  zIndex: {
    base: 0,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },
};

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type ColorShade = 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900;
export type SpacingToken = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl';
export type FontSizeToken = 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl';
export type FontWeightToken = 'normal' | 'medium' | 'semibold' | 'bold';
export type RadiusToken = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get a color from the design tokens
 * @param colorPath - Path to color (e.g., 'primary.600', 'success', 'gray.500')
 * @returns CSS color string
 */
export function getColor(colorPath: string): string {
  const parts = colorPath.split('.');
  let value: any = DESIGN_TOKENS.colors;

  for (const part of parts) {
    value = value[part];
    if (value === undefined) {
      console.warn(`Color not found: ${colorPath}`);
      return '#000000';
    }
  }

  return value as string;
}

/**
 * Get spacing value
 * @param token - Spacing token
 * @returns Numeric spacing value
 */
export function getSpacing(token: SpacingToken): number {
  return DESIGN_TOKENS.spacing[token] || 0;
}

/**
 * Get font size
 * @param token - Font size token
 * @returns Numeric font size
 */
export function getFontSize(token: FontSizeToken): number {
  return DESIGN_TOKENS.typography.size[token] || 16;
}

/**
 * Get font weight
 * @param token - Font weight token
 * @returns Numeric font weight
 */
export function getFontWeight(token: FontWeightToken): number {
  return DESIGN_TOKENS.typography.weight[token] || 400;
}

/**
 * Get border radius
 * @param token - Border radius token
 * @returns Numeric border radius
 */
export function getRadius(token: RadiusToken): number {
  return DESIGN_TOKENS.radius[token] || 0;
}

/**
 * Create a React Native StyleSheet-compatible style object
 * Only includes properties that React Native supports
 */
export function createRNStyles(styles: Record<string, any>): Record<string, any> {
  return styles;
}

// =============================================================================
// COMMON STYLE PRESETS
// =============================================================================

export const commonStyles = {
  // Containers
  container: {
    padding: DESIGN_TOKENS.spacing.md,
  } as const,

  card: {
    backgroundColor: '#ffffff',
    borderRadius: DESIGN_TOKENS.radius.md,
    padding: DESIGN_TOKENS.spacing.md,
    ...DESIGN_TOKENS.shadow.sm,
  } as const,

  // Text
  heading: {
    fontSize: DESIGN_TOKENS.typography.size.xl,
    fontWeight: DESIGN_TOKENS.typography.weight.bold as any,
    color: DESIGN_TOKENS.colors.gray[900],
  } as const,

  body: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    color: DESIGN_TOKENS.colors.gray[700],
  } as const,

  caption: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: DESIGN_TOKENS.colors.gray[500],
  } as const,

  // Buttons
  button: {
    paddingVertical: DESIGN_TOKENS.spacing.sm,
    paddingHorizontal: DESIGN_TOKENS.spacing.lg,
    borderRadius: DESIGN_TOKENS.radius.md,
    backgroundColor: DESIGN_TOKENS.colors.primary[600],
  } as const,

  buttonSecondary: {
    paddingVertical: DESIGN_TOKENS.spacing.sm,
    paddingHorizontal: DESIGN_TOKENS.spacing.lg,
    borderRadius: DESIGN_TOKENS.radius.md,
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: DESIGN_TOKENS.colors.gray[300],
  } as const,

  // Inputs
  input: {
    paddingVertical: DESIGN_TOKENS.spacing.sm,
    paddingHorizontal: DESIGN_TOKENS.spacing.md,
    borderRadius: DESIGN_TOKENS.radius.md,
    borderWidth: 1,
    borderColor: DESIGN_TOKENS.colors.gray[300],
    fontSize: DESIGN_TOKENS.typography.size.base,
  } as const,

  // Spacing utilities
  m_xs: { margin: DESIGN_TOKENS.spacing.xs } as const,
  m_sm: { margin: DESIGN_TOKENS.spacing.sm } as const,
  m_md: { margin: DESIGN_TOKENS.spacing.md } as const,
  m_lg: { margin: DESIGN_TOKENS.spacing.lg } as const,

  p_xs: { padding: DESIGN_TOKENS.spacing.xs } as const,
  p_sm: { padding: DESIGN_TOKENS.spacing.sm } as const,
  p_md: { padding: DESIGN_TOKENS.spacing.md } as const,
  p_lg: { padding: DESIGN_TOKENS.spacing.lg } as const,
};

export default DESIGN_TOKENS;
