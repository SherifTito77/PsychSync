/**
 * Design Token API
 *
 * Provides type-safe access to design system tokens.
 * Use these utilities instead of hardcoded values to ensure consistency.
 *
 * @example
 * // ❌ BAD: Hardcoded values
 * style={{ color: '#2563eb', padding: '16px' }}
 *
 * // ✅ GOOD: Design tokens
 * style={{ color: tokens.color.primary(600), padding: tokens.spacing.md }}
 */

import { clsx, type ClassValue } from 'clsx';

/**
 * Design token utilities for inline styles
 */
export const tokens = {
  /**
   * Color tokens
   * @example tokens.color.primary(600) → 'var(--color-primary-600)'
   */
  color: {
    // Primary colors (blue scale)
    primary: (shade: 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 = 600) =>
      `var(--color-primary-${shade})`,

    // Semantic colors
    success: () => 'var(--color-success)',
    successLight: () => 'var(--color-success-light)',
    warning: () => 'var(--color-warning)',
    warningLight: () => 'var(--color-warning-light)',
    error: () => 'var(--color-error)',
    errorLight: () => 'var(--color-error-light)',
    info: () => 'var(--color-info)',
    infoLight: () => 'var(--color-info-light)',

    // Gray scale
    gray: (shade: 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 = 600) =>
      `var(--color-gray-${shade})`,

    // Clinical colors
    clinicalCrisis: () => 'var(--color-clinical-crisis)',
    clinicalModerate: () => 'var(--color-clinical-moderate)',
    clinicalMild: () => 'var(--color-clinical-mild)',
    clinicalStable: () => 'var(--color-clinical-stable)',

    // Gamification tier colors
    tierBronze: () => 'var(--color-tier-bronze)',
    tierSilver: () => 'var(--color-tier-silver)',
    tierGold: () => 'var(--color-tier-gold)',
    tierPlatinum: () => 'var(--color-tier-platinum)',
    tierDiamond: () => 'var(--color-tier-diamond)',
  },

  /**
   * Spacing tokens (4px base unit)
   * @example tokens.spacing.md → 'var(--spacing-md)' (16px)
   */
  spacing: {
    xs: () => 'var(--spacing-xs)',   // 4px
    sm: () => 'var(--spacing-sm)',   // 8px
    md: () => 'var(--spacing-md)',   // 16px
    lg: () => 'var(--spacing-lg)',   // 24px
    xl: () => 'var(--spacing-xl)',   // 32px
    xl2: () => 'var(--spacing-2xl)', // 48px
    xl3: () => 'var(--spacing-3xl)', // 64px
    xl4: () => 'var(--spacing-4xl)', // 96px
    xl5: () => 'var(--spacing-5xl)', // 20px
  },

  /**
   * Typography tokens
   * @example tokens.typography.size.lg → 'var(--font-size-lg)' (18px)
   */
  typography: {
    size: {
      xs: () => 'var(--font-size-xs)',   // 12px
      sm: () => 'var(--font-size-sm)',   // 14px
      base: () => 'var(--font-size-base)', // 16px
      lg: () => 'var(--font-size-lg)',   // 18px
      xl: () => 'var(--font-size-xl)',   // 20px
      xl2: () => 'var(--font-size-2xl)', // 24px
      xl3: () => 'var(--font-size-3xl)', // 30px
      xl4: () => 'var(--font-size-4xl)', // 36px
      xl5: () => 'var(--font-size-5xl)', // 48px
    },
    weight: {
      normal: () => 'var(--font-weight-normal)',   // 400
      medium: () => 'var(--font-weight-medium)',   // 500
      semibold: () => 'var(--font-weight-semibold)', // 600
      bold: () => 'var(--font-weight-bold)',      // 700
      extrabold: () => 'var(--font-weight-extrabold)', // 800
    },
  },

  /**
   * Border radius tokens
   * @example tokens.radius.md → 'var(--radius-md)' (8px)
   */
  radius: {
    sm: () => 'var(--radius-sm)',   // 4px
    md: () => 'var(--radius-md)',   // 8px
    lg: () => 'var(--radius-lg)',   // 12px
    xl: () => 'var(--radius-xl)',   // 16px
    xl2: () => 'var(--radius-2xl)', // 24px
    full: () => 'var(--radius-full)', // 9999px
  },

  /**
   * Shadow tokens
   * @example tokens.shadow.md → 'var(--shadow-md)'
   */
  shadow: {
    sm: () => 'var(--shadow-sm)',
    md: () => 'var(--shadow-md)',
    lg: () => 'var(--shadow-lg)',
    xl: () => 'var(--shadow-xl)',
    xl2: () => 'var(--shadow-2xl)',
    inner: () => 'var(--shadow-inner)',
  },

  /**
   * Z-index tokens
   * @example tokens.zIndex.modal → 'var(--z-modal)' (1050)
   */
  zIndex: {
    dropdown: () => 'var(--z-dropdown)',       // 1000
    sticky: () => 'var(--z-sticky)',          // 1020
    fixed: () => 'var(--z-fixed)',            // 1030
    modalBackdrop: () => 'var(--z-modal-backdrop)', // 1040
    modal: () => 'var(--z-modal)',            // 1050
    popover: () => 'var(--z-popover)',        // 1060
    tooltip: () => 'var(--z-tooltip)',        // 1070
  },

  /**
   * Transition tokens
   * @example tokens.transition.base → 'var(--transition-base)' (200ms)
   */
  transition: {
    fast: () => 'var(--transition-fast)',   // 150ms
    base: () => 'var(--transition-base)',   // 200ms
    slow: () => 'var(--transition-slow)',   // 300ms
  },
} as const;

/**
 * Create inline styles object from design tokens
 * @example
 * const buttonStyle = createStyles({
 *   backgroundColor: tokens.color.primary(600),
 *   padding: tokens.spacing.md,
 *   borderRadius: tokens.radius.md,
 * })
 */
export function createStyles(styles: Record<string, string>) {
  return styles;
}

/**
 * Tailwind class name helper with type safety
 * Combines clsx with design system awareness
 *
 * @example
 * cn('px-4 py-2', isActive && 'bg-blue-600', 'hover:bg-blue-700')
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Convert spacing units to pixels (for JS calculations)
 * @example spacingToPx('md') → 16
 */
export function spacingToPx(unit: keyof typeof tokens.spacing): number {
  const spacingMap = {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xl2: 48,
    xl3: 64,
    xl4: 96,
    xl5: 20,
  };
  return spacingMap[unit];
}

/**
 * Check if a color value is a design token reference
 */
export function isDesignTokenColor(value: string): boolean {
  return value.startsWith('var(--color-');
}

/**
 * Validate if a value is on the design token scale
 */
export function isOnSpacingScale(px: number): boolean {
  return px % 4 === 0 && px >= 4 && px <= 96;
}

/**
 * Get the nearest spacing token for a given pixel value
 */
export function getNearestSpacing(px: number): string {
  const spacingOptions = [4, 8, 12, 16, 20, 24, 32, 48, 64, 96];
  const nearest = spacingOptions.reduce((prev, curr) =>
    Math.abs(curr - px) < Math.abs(prev - px) ? curr : prev
  );
  return `var(--spacing-${nearest === 4 ? 'xs' : nearest === 8 ? 'sm' : nearest === 16 ? 'md' : nearest === 24 ? 'lg' : nearest === 32 ? 'xl' : nearest === 48 ? '2xl' : nearest === 64 ? '3xl' : nearest === 96 ? '4xl' : '5xl'})`;
}
