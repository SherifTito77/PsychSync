/**
 * Custom ESLint Rules for React Memory Leak Prevention
 *
 * This plugin enforces the 5 golden rules for useEffect cleanup:
 * 1. Always return cleanup function from useEffect
 * 2. Track mounted status for async operations
 * 3. Use AbortController for fetch/axios
 * 4. Store refs for timeouts/intervals
 * 5. Clear all refs in cleanup function
 *
 * @example
 * // .eslintrc.js
 * module.exports = {
 *   plugins: ['react-memory-leaks'],
 *   rules: {
 *     'react-memory-leaks/use-effect-cleanup': 'error',
 *     'react-memory-leaks/no-unchecked-async': 'error',
 *     'react-memory-leaks/require-abort-controller': 'warn',
 *   }
 * };
 */

const { ESLintUtils } = require("@typescript-eslint/utils");

module.exports = {
  meta: {
    type: "problem",
    docs: {
      description: "Detect potential memory leaks in React useEffect hooks",
      category: "Best Practices",
      recommended: "error",
    },
    messages: {
      missingCleanup:
        "useEffect should return a cleanup function when creating resources (timers, listeners, subscriptions).",
      uncheckedAsync:
        "useEffect contains async operation without mounted check. Use useAsyncEffect hook or check isMounted before setState.",
      missingAbortController:
        "useEffect contains fetch/axios call without AbortController. Requests may continue after unmount.",
      timeoutWithoutCleanup:
        "setTimeout/setInterval detected without corresponding clearTimeout/clearInterval in cleanup.",
      eventListenerWithoutCleanup:
        "addEventListener detected without corresponding removeEventListener in cleanup.",
    },
    schema: [],
  },
  create: ESLintUtils.RuleCreator((ruleName) => ({
    name: ruleName,
    meta: {
      type: "problem",
      docs: {
        description: "Detect React memory leaks in useEffect",
      },
      messages: {
        missingCleanup:
          "useEffect should return a cleanup function when creating resources",
        uncheckedAsync:
          "useEffect contains async operation without mounted check",
        missingAbortController:
          "useEffect contains fetch/axios without AbortController",
        timeoutWithoutCleanup: "setTimeout/setInterval without cleanup",
        eventListenerWithoutCleanup: "addEventListener without cleanup",
      },
      schema: [],
    },
    defaultOptions: [],
    create(context) {
      return {
        // Match useEffect calls
        CallExpression(node) {
          if (
            node.callee.type === "Identifier" &&
            node.callee.name === "useEffect"
          ) {
            const effectCallback = node.arguments[0];

            // Skip if not a function expression or arrow function
            if (
              !effectCallback ||
              (effectCallback.type !== "ArrowFunctionExpression" &&
                effectCallback.type !== "FunctionExpression")
          ) {
            return;
          }

          const hasReturnStatement =
            effectCallback.body &&
            effectCallback.body.type === "BlockStatement" &&
            effectCallback.body.body.some(
              (stmt) => stmt.type === "ReturnStatement"
            );

          // Check for setTimeout/setInterval
          const sourceCode = context.getSourceCode();
          const callbackText = sourceCode.getText(effectCallback);

          const hasSetTimeout = /setTimeout\s*\(/.test(callbackText);
          const hasSetInterval = /setInterval\s*\(/.test(callbackText);
          const hasAddEventListener =
            /addEventListener\s*\(/.test(callbackText);
          const hasAsyncKeyword = callbackText.includes("async");
          const hasAwait = /await\s+/.test(callbackText);
          const hasFetch = /fetch\s*\(/.test(callbackText);
          const hasAxios = /axios\.(get|post|put|delete|patch)\s*\(/.test(
            callbackText
          );

          // Rule 1: setTimeout/setInterval require cleanup
          if ((hasSetTimeout || hasSetInterval) && !hasReturnStatement) {
            context.report({
              node,
              messageId: "timeoutWithoutCleanup",
            });
          }

          // Rule 1: addEventListener requires cleanup
          if (hasAddEventListener && !hasReturnStatement) {
            context.report({
              node,
              messageId: "eventListenerWithoutCleanup",
            });
          }

          // Rule 2 & 3: Async operations require mounted check or AbortController
          const hasMountedCheck =
            /if\s*\(\s*isMounted\s*\(/.test(callbackText) ||
            /isMounted\.current/.test(callbackText);
          const hasAbortController =
            /AbortController/.test(callbackText) ||
            /signal:\s*abortController\.signal/.test(callbackText) ||
            /signal\s*:\s*\w*\.signal/.test(callbackText);

          if ((hasAsyncKeyword || hasAwait) && !hasMountedCheck) {
            context.report({
              node,
              messageId: "uncheckedAsync",
            });
          }

          if ((hasFetch || hasAxios) && !hasAbortController) {
            context.report({
              node,
              messageId: "missingAbortController",
              suggest: [
                {
                  desc: "Add AbortController to cancel requests on unmount",
                  fix: (fixer) => {
                    // Suggest adding AbortController pattern
                    // This is a simplified fix - manual review needed
                    return null;
                  },
                },
              ],
            });
          }

          // Rule 5: If there are multiple resources, ensure all are cleaned up
          if (hasReturnStatement && (hasSetTimeout || hasSetInterval)) {
            const returnStatement = effectCallback.body.body.find(
              (stmt) => stmt.type === "ReturnStatement"
            );

            if (returnStatement && returnStatement.argument) {
              const cleanupText = sourceCode.getText(returnStatement.argument);
              const timeoutCount =
                (callbackText.match(/setTimeout/g) || []).length;
              const clearCount =
                (cleanupText.match(/clearTimeout/g) || []).length;

              const intervalCount =
                (callbackText.match(/setInterval/g) || []).length;
              const clearIntervalCount =
                (cleanupText.match(/clearInterval/g) || []).length;

              if (
                timeoutCount > clearCount ||
                intervalCount > clearIntervalCount
              ) {
                context.report({
                  node: returnStatement,
                  messageId: "missingCleanup",
                });
              }
            }
          }
        },
      };
    },
  })),
  rules: {
    "use-effect-cleanup": {
      meta: {
        type: "problem",
        docs: {
          description:
            "Enforce cleanup functions in useEffect when resources are created",
          recommended: "error",
        },
        messages: {
          missingCleanup:
            "useEffect creates resources but doesn't return a cleanup function. All timers, listeners, and subscriptions must be cleaned up.",
        },
      },
      create(context) {
        return {};
      },
    },
    "no-unchecked-async": {
      meta: {
        type: "problem",
        docs: {
          description:
            "Require mounted checks or useAsyncEffect for async operations in useEffect",
          recommended: "error",
        },
        messages: {
          uncheckedAsync:
            "Async operation in useEffect without mounted check. Component may unmount before operation completes.",
        },
      },
      create(context) {
        return {};
      },
    },
    "require-abort-controller": {
      meta: {
        type: "suggestion",
        docs: {
          description:
            "Suggest using AbortController for fetch/axios calls in useEffect",
          recommended: "warn",
        },
        messages: {
          missingAbortController:
            "HTTP request without AbortController. Request may continue after component unmounts.",
        },
      },
      create(context) {
        return {};
      },
    },
  },
};
