import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import react from "eslint-plugin-react";
import jsxA11y from "eslint-plugin-jsx-a11y";
import importPlugin from "eslint-plugin-import";
import { includeIgnoreFile } from "@eslint/compat";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const gitignorePath = path.join(__dirname, ".gitignore");

export default [
  // Include .gitignore patterns
  includeIgnoreFile(gitignorePath),

  // Global ignores
  {
    ignores: [
      "dist",
      "build",
      "node_modules",
      "coverage",
      "*.config.js",
      "*.config.ts",
      "vite-env.d.ts",
    ],
  },

  // Base JavaScript/JSX configuration
  {
    files: ["**/*.{js,jsx}"],
    extends: [js.configs.recommended],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      // Error prevention
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "no-var": "error",
      "prefer-const": "error",
      "prefer-arrow-callback": "error",
      "prefer-template": "error",
    },
  },

  // TypeScript/TSX configuration
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parser: tsparser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        project: "./tsconfig.json",
        tsconfigRootDir: __dirname,
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
      react: react,
      "jsx-a11y": jsxA11y,
      import: importPlugin,
    },
    settings: {
      react: {
        version: "detect",
      },
      "import/resolver": {
        typescript: {
          alwaysTryTypes: true,
          project: "./tsconfig.json",
        },
      },
    },
    rules: {
      // TypeScript recommended rules
      ...tseslint.configs.recommended.rules,

      // React recommended rules
      ...react.configs.recommended.rules,

      // JSX Accessibility rules
      ...jsxA11y.configs.recommended.rules,

      // Import plugin rules
      ...importPlugin.configs.recommended.rules,
      ...importPlugin.configs.typescript.rules,

      // TypeScript-specific rules
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          ignoreRestSiblings: true,
        },
      ],
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-non-null-assertion": "warn",
      "@typescript-eslint/consistent-type-imports": [
        "error",
        {
          prefer: "type-imports",
          disallowTypeAnnotations: false,
        },
      ],
      "@typescript-eslint/await-thenable": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/no-unnecessary-type-assertion": "error",
      "@typescript-eslint/prefer-nullish-coalescing": "error",
      "@typescript-eslint/prefer-optional-chain": "error",
      "@typescript-eslint/strict-boolean-expressions": "warn",

      // React rules
      "react/react-in-jsx-scope": "off", // Not needed with React 17+
      "react/prop-types": "off", // Using TypeScript instead
      "react/display-name": "off", // Not needed with TypeScript
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "react/jsx-uses-react": "off",
      "react/jsx-no-target-blank": "error",
      "react/jsx-key": ["error", { checkFragmentShorthand: true }],
      "react/no-array-index-key": "warn",
      "react/no-unescaped-entities": "error",
      "react/self-closing-comp": "error",
      "react/jsx-curly-brace-presence": [
        "error",
        { props: "never", children: "never" },
      ],

      // Import rules
      "import/order": [
        "error",
        {
          groups: [
            "builtin",
            "external",
            "internal",
            "parent",
            "sibling",
            "index",
          ],
          "newlines-between": "always",
          alphabetize: {
            order: "asc",
            caseInsensitive: true,
          },
          pathGroups: [
            { pattern: "react", group: "external", position: "before" },
            { pattern: "@/**", group: "internal" },
            { pattern: "@components/**", group: "internal" },
            { pattern: "@pages/**", group: "internal" },
            { pattern: "@services/**", group: "internal" },
            { pattern: "@hooks/**", group: "internal" },
            { pattern: "@utils/**", group: "internal" },
            { pattern: "@types/**", group: "internal" },
          ],
          pathGroupsExcludedImportTypes: ["react", "builtin"],
        },
      ],
      "import/no-unresolved": "off", // TypeScript handles this
      "import/no-cycle": "warn",
      "import/no-duplicates": "error",
      "import/no-unused-modules": "warn",
      "import/no-relative-parent-imports": "error",

      // Accessibility rules
      "jsx-a11y/anchor-is-valid": [
        "error",
        {
          components: ["Link"],
          specialLink: ["to", "hrefLeft", "hrefRight"],
          aspects: ["noHref", "invalidHref", "preferButton"],
        },
      ],
      "jsx-a11y/click-events-have-key-events": "warn",
      "jsx-a11y/no-static-element-interactions": "warn",
      "jsx-a11y/aria-props": "error",
      "jsx-a11y/aria-proptypes": "error",
      "jsx-a11y/aria-unsupported-elements": "error",
      "jsx-a11y/role-has-required-aria-props": "error",
      "jsx-a11y/role-supports-aria-props": "error",

      // Code quality rules
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "no-alert": "warn",
      "no-var": "error",
      "prefer-const": "error",
      "prefer-arrow-callback": "error",
      "prefer-template": "error",
      "no-duplicate-imports": "error",
      "no-useless-concat": "error",
      "no-useless-return": "error",
      "eqeqeq": ["error", "always"],
      "curly": ["error", "all"],
    },
  },

  // Test files specific configuration
  {
    files: ["**/*.test.{ts,tsx}", "**/*.spec.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-non-null-assertion": "off",
      "no-console": "off",
    },
  },

  // Configuration files
  {
    files: [
      "**/*.config.js",
      "**/*.config.ts",
      "vite.config.ts",
      "tailwind.config.js",
      "postcss.config.js",
    ],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "no-console": "off",
    },
  },
];

/*
 * ==============================================================================
 * LINTING RULES RATIONALE
 * ==============================================================================
 *
 * This configuration enforces:
 *
 * 1. Type Safety:
 *    - Strict TypeScript rules catch type errors at compile time
 *    - No explicit 'any' unless absolutely necessary
 *    - Proper async/await usage
 *
 * 2. React Best Practices:
 *    - Hooks rules prevent common bugs
 *    - Proper key usage for lists
 *    - No console statements in production code
 *
 * 3. Accessibility (a11y):
 *    - ARIA attributes must be valid
 *    - Interactive elements must be keyboard accessible
 *    - Proper semantic HTML usage
 *
 * 4. Import Organization:
 *    - Consistent import ordering
 *    - Type imports separated from value imports
 *    - Path aliases (@/ etc) enforced
 *
 * 5. Code Quality:
 *    - No unused variables
 *    - Prefer const over let/var
 *    - No duplicate imports
 *
 * Team Adoption Guidelines:
 * - Run `npm run lint` to check for issues
 * - Run `npm run lint:fix` to auto-fix most issues
 * - Run `npm run type-check` to verify TypeScript types
 * - Most rules have auto-fix available
 * - For accessibility warnings, review semantic HTML structure
 * - For import errors, check tsconfig.json paths configuration
 *
 * Exceptions:
 * - Test files (.test.ts, .spec.ts) have relaxed rules for 'any' and console
 * - Config files have relaxed rules for 'any'
 * - Legacy code may need // eslint-disable-next-line comments (use sparingly)
 */
