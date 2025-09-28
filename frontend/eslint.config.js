
import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import { defineConfig, globalIgnores } from "eslint/config";

export default defineConfig([
  // Ignore dist folder globally
  globalIgnores(["dist"]),
  {
    // For JS/JSX files
    files: ["**/*.{js,jsx}"],
    extends: [
      js.configs.recommended,
      reactHooks.configs["recommended-latest"],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: "latest",
        ecmaFeatures: { jsx: true },
        sourceType: "module",
      },
    },
    rules: {
      "no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z_]" }],
    },
  },
  {
    // For TS/TSX files
    files: ["**/*.{ts,tsx}"],
    parser: "@typescript-eslint/parser",
    parserOptions: {
      ecmaVersion: 2020,
      sourceType: "module",
      ecmaFeatures: { jsx: true },
    },
    extends: [
      "eslint:recommended",
      "plugin:react/recommended",
      "plugin:@typescript-eslint/recommended",
      "prettier",
    ],
    plugins: ["react", "@typescript-eslint"],
    settings: {
      react: {
        version: "detect",
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z_]" }],
    },
  },
]);

// import js from "@eslint/js";
// import globals from "globals";
// import reactHooks from "eslint-plugin-react-hooks";
// import reactRefresh from "eslint-plugin-react-refresh";
// import { defineConfig, globalIgnores } from "eslint/config";

// export default defineConfig([
//   globalIgnores(["dist"]),
//   {
//     files: ["**/*.{js,jsx}"],
//     extends: [
//       js.configs.recommended,
//       reactHooks.configs["recommended-latest"],
//       reactRefresh.configs.vite,
//     ],
//     languageOptions: {
//       ecmaVersion: 2020,
//       globals: globals.browser,
//       parserOptions: {
//         ecmaVersion: "latest",
//         ecmaFeatures: { jsx: true },
//         sourceType: "module",
//       },
//     },
//     rules: {
//       "no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z_]" }],
//     },
//   },
// ]);


// export default {
//   parser: "@typescript-eslint/parser",
//   parserOptions: {
//     ecmaVersion: 2020,
//     sourceType: "module",
//   },
//   extends: [
//     "eslint:recommended",
//     "plugin:react/recommended",
//     "plugin:@typescript-eslint/recommended",
//     "prettier",
//   ],
//   plugins: ["react", "@typescript-eslint"],
//   settings: {
//     react: {
//       version: "detect",
//     },
//   },
//   ignorePatterns: ["node_modules/", "dist/"],
// };
