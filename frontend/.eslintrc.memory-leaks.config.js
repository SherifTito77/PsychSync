/**
 * ESLint Configuration for React Memory Leak Prevention
 *
 * Usage: Add this to your .eslintrc.js or eslint.config.js
 *
 * @example
 * ```js
 * module.exports = {
 *   extends: [
 *     'eslint:recommended',
 *     'plugin:react-memory-leaks/recommended'
 *   ],
 *   plugins: ['react-memory-leaks'],
 *   rules: {
 *     'react-memory-leaks/use-effect-cleanup': 'error',
 *     'react-memory-leaks/no-unchecked-async': 'error',
 *     'react-memory-leaks/require-abort-controller': 'warn'
 *   }
 * };
 * ```
 */

module.exports = {
  plugins: ['react-memory-leaks'],
  extends: ['plugin:react-memory-leaks/recommended'],
  rules: {
    // Error: Missing cleanup function in useEffect
    'react-memory-leaks/use-effect-cleanup': 'error',

    // Error: Async operations without mounted check
    'react-memory-leaks/no-unchecked-async': 'error',

    // Warning: HTTP requests without AbortController
    'react-memory-leaks/require-abort-controller': 'warn',

    // Auto-fix: Suggest using existing hooks
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
