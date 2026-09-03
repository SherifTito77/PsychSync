/**
 * useAccessibilityMotion Hook
 *
 * Provides animation configurations that respect user's motion preferences.
 * Uses Framer Motion's useReducedMotion under the hood.
 *
 * @example
 * const shouldReduceMotion = useAccessibilityMotion();
 * const transition = useAccessibilityTransition();
 *
 * <motion.div
 *   animate={{ opacity: 1 }}
 *   transition={transition}
 * />
 */

import { useReducedMotion as framerUseReducedMotion, type Transition } from 'framer-motion';

/**
 * Hook that returns whether the user prefers reduced motion
 */
export function useAccessibilityMotion(): boolean {
  const prefersReducedMotion = framerUseReducedMotion();

  // Also check CSS media query for non-Framer animations
  const [cssPrefersReduced, setCssPrefersReduced] = React.useState(false);

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setCssPrefersReduced(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setCssPrefersReduced(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion || cssPrefersReduced;
}

/**
 * Hook that returns appropriate transition config based on motion preference
 *
 * @param customTransition - Custom transition to use when motion is allowed
 * @returns Transition object (duration: 0 if reduced motion preferred)
 */
export function useAccessibilityTransition(
  customTransition?: Transition
): Transition {
  const shouldReduceMotion = useAccessibilityMotion();

  if (shouldReduceMotion) {
    return { duration: 0 };
  }

  return customTransition || { duration: 0.3 };
}

/**
 * Hook that returns spring config tuned for accessibility
 *
 * @param config - Spring configuration
 * @returns Spring config with adjusted damping for reduced motion
 */
export function useAccessibilitySpring(config: {
  stiffness?: number;
  damping?: number;
} = {}): { type: 'spring'; stiffness: number; damping: number } | { duration: number } {
  const shouldReduceMotion = useAccessibilityMotion();

  if (shouldReduceMotion) {
    return { duration: 0 };
  }

  // Default spring values with better damping than Framer defaults
  const { stiffness = 300, damping = 40 } = config;

  return {
    type: 'spring',
    stiffness,
    damping,
  };
}

/**
 * Hook that returns animation variants respecting reduced motion
 *
 * @param variants - Animation variants
 * @returns Simplified variants (fade only) if reduced motion preferred
 */
export function useAccessibilityVariants<T extends string>(
  variants: Record<T, any>
): Record<T, any> {
  const shouldReduceMotion = useAccessibilityMotion();

  if (shouldReduceMotion) {
    // Return simplified variants with only opacity changes
    const simplified: Record<string, any> = {};
    for (const key in variants) {
      simplified[key] = {
        opacity: variants[key].opacity ?? (variants[key].scale ? 0 : 1),
      };
    }
    return simplified as Record<T, any>;
  }

  return variants;
}

// Import React for the internal hook
import React from 'react';
