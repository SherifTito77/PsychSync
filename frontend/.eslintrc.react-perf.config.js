/**
 * React Performance Rules Configuration
 * Catches expensive re-renders caused by anonymous functions and objects
 *
 * Run with: eslint --config .eslintrc.react-perf.config.js src/
 */

module.exports = {
  extends: [
    'plugin:react-hooks/recommended',
    'plugin:react/recommended',
    'plugin:jsx-a11y/recommended'
  ],
  plugins: [
    'react',
    'react-hooks',
    'jsx-a11y'
  ],
  rules: {
    // ==========================================
    // REACT PERFORMANCE RULES
    // ==========================================

    // Prevent missing dependencies in hooks
    'react-hooks/exhaustive-deps': 'warn',

    // Prevent inline functions in JSX props (HIGH IMPACT)
    'react/jsx-no-bind': 'warn',

    // Prevent destructuring of props in function declarations
    'react/no-destructuring': 'off', // Keep off for convenience

    // Prevent using this.state within setState
    'react/no-access-state-in-setstate': 'error',

    // Prevent direct mutation of this.state
    'react/no-did-update-set-state': 'warn',

    // Prevent usage of setState in componentDidMount
    'react/no-did-mount-set-state': 'warn',

    // Prevent usage of unknown properties
    'react/no-unknown-property': 'error',

    // Prevent missing props validation
    'react/prop-types': 'off', // TypeScript handles this

    // ==========================================
    // JSX PERFORMANCE PATTERNS
    // ==========================================

    // Enforce curly braces or no curly braces for JSX props
    'react/jsx-curly-brace-presence': ['warn', {
      props: 'never',
      children: 'never'
    }],

    // Enforce shorthand or standard form for React fragments
    'react/jsx-fragments': ['warn', 'syntax'],

    // Prevent duplicate props in JSX
    'react/jsx-no-duplicate-props': 'error',

    // Prevent usage of string literals in JSX (use {} instead)
    'react/jsx-no-literals': 'off', // Keep off for convenience

    // Prevent usage of unsafe target='_blank'
    'react/jsx-no-target-blank': 'error',

    // Enforce PascalCase for user-defined JSX components
    'react/jsx-pascal-case': ['warn', {
      allowAllCaps: true,
      ignore: []
    }],

    // Prevent React to be marked as unused
    'react/jsx-uses-react': 'error',

    // Prevent variables used in JSX to be marked as unused
    'react/jsx-uses-vars': 'error',

    // ==========================================
    // HOOKS RULES
    // ==========================================

    // Only allow Hooks at the top level
    'react-hooks/rules-of-hooks': 'error',

    // ==========================================
    // CUSTOM PERFORMANCE RULES
    // ==========================================

    // Detect inline styles that should be memoized
    'no-inline-styles': 'off' // Custom rule below

  },
  overrides: [
    {
      // Performance-critical directories
      files: [
        'src/components/lists/**/*.tsx',
        'src/components/tables/**/*.tsx',
        'src/components/charts/**/*.tsx',
        'src/components/dashboard/**/*.tsx'
      ],
      rules: {
        // Stricter rules for performance-critical components
        'react-hooks/exhaustive-deps': 'error',
        'react/jsx-no-bind': 'error',
      }
    }
  ]
};
