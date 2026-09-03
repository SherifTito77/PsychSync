/**
 * Custom ESLint Plugin for Memory Leak Prevention
 *
 * This plugin detects common React memory leaks:
 * - Missing cleanup in useEffect with timers/intervals
 * - Event listeners added without removal
 * - WebSocket connections not cleaned up
 * - Subscriptions not unsubscribed
 *
 * @version 1.0.0
 * @license MIT
 */

import js from "@eslint/js";

/**
 * Rule: Detect setInterval/setTimeout without cleanup in useEffect
 */
const noUncleanedTimersRule = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Ensure timers and intervals are cleaned up in useEffect',
      category: 'Best Practices',
      recommended: 'error',
    },
    messages: {
      missingCleanup: 'Potential memory leak: {{timerType}} created without cleanup. Use: const id = {{timerType}}(...); return () => clear{{timerTypeShort}}(id);',
      missingReturn: 'useEffect creates {{timerType}} but lacks a return cleanup function',
    },
    schema: [],
  },
  create(context) {
    return {
      CallExpression(node) {
        // Check for setInterval or setTimeout calls
        if (
          node.callee.type === 'Identifier' &&
          (node.callee.name === 'setInterval' || node.callee.name === 'setTimeout')
        ) {
          // Find the parent useEffect
          let parent = node.parent;
          let foundUseEffect = false;

          while (parent && !foundUseEffect) {
            if (parent.type === 'CallExpression' &&
                parent.callee.type === 'Identifier' &&
                parent.callee.name === 'useEffect') {
              foundUseEffect = true;

              // Check if useEffect has a return statement
              const useEffectArg = parent.arguments[0];
              if (useEffectArg && useEffectArg.type === 'ArrowFunctionExpression') {
                const hasReturn = useEffectArg.body.body?.some(
                  stmt => stmt.type === 'ReturnStatement'
                );

                if (!hasReturn) {
                  context.report({
                    node,
                    messageId: 'missingCleanup',
                    data: {
                      timerType: node.callee.name,
                      timerTypeShort: node.callee.name === 'setInterval' ? 'Interval' : 'Timeout',
                    },
                  });
                }
              }
            }
            parent = parent.parent;
          }
        }
      },
    };
  },
};

/**
 * Rule: Detect addEventListener without removeEventListener
 */
const noUncleanedEventListenersRule = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Ensure event listeners are cleaned up in useEffect',
      category: 'Best Practices',
      recommended: 'error',
    },
    messages: {
      missingCleanup: 'Potential memory leak: Event listener "{{event}}" added without cleanup. Add: return () => target.removeEventListener("{{event}}", handler);',
    },
    schema: [],
  },
  create(context) {
    return {
      CallExpression(node) {
        // Check for addEventListener calls
        if (
          node.callee.type === 'MemberExpression' &&
          node.callee.property.name === 'addEventListener'
        ) {
          // Get the event name
          const eventName = node.arguments[0];
          const eventValue = eventName.type === 'Literal' ? eventName.value : 'unknown';

          // Find the parent useEffect
          let parent = node.parent;
          let foundUseEffect = false;

          while (parent && !foundUseEffect) {
            if (parent.type === 'CallExpression' &&
                parent.callee.type === 'Identifier' &&
                parent.callee.name === 'useEffect') {
              foundUseEffect = true;

              // Check if useEffect has a return statement with removeEventListener
              const useEffectArg = parent.arguments[0];
              if (useEffectArg && useEffectArg.type === 'ArrowFunctionExpression') {
                const hasCleanup = useEffectArg.body.body?.some(
                  stmt =>
                    stmt.type === 'ReturnStatement' &&
                    context.getSourceCode().getText(stmt).includes('removeEventListener')
                );

                if (!hasCleanup) {
                  context.report({
                    node,
                    messageId: 'missingCleanup',
                    data: { event: eventValue },
                  });
                }
              }
            }
            parent = parent.parent;
          }
        }
      },
    };
  },
};

/**
 * Rule: Detect WebSocket connections without cleanup
 */
const noUncleanedWebsocketsRule = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Ensure WebSocket connections are cleaned up',
      category: 'Best Practices',
      recommended: 'error',
    },
    messages: {
      missingCleanup: 'Potential memory leak: WebSocket created without cleanup. Use: return () => ws.close();',
      useRefRecommended: 'WebSocket should be stored in useRef: const wsRef = useRef(null);',
    },
    schema: [],
  },
  create(context) {
    return {
      NewExpression(node) {
        // Check for WebSocket instantiation
        if (node.callee.name === 'WebSocket') {
          // Find the parent useEffect
          let parent = node.parent;
          let foundUseEffect = false;

          while (parent && !foundUseEffect) {
            if (parent.type === 'CallExpression' &&
                parent.callee.type === 'Identifier' &&
                parent.callee.name === 'useEffect') {
              foundUseEffect = true;

              // Check if useEffect has a return statement with close()
              const useEffectArg = parent.arguments[0];
              if (useEffectArg && useEffectArg.type === 'ArrowFunctionExpression') {
                const hasCleanup = useEffectArg.body.body?.some(
                  stmt =>
                    stmt.type === 'ReturnStatement' &&
                    context.getSourceCode().getText(stmt).includes('.close()')
                );

                if (!hasCleanup) {
                  context.report({
                    node,
                    messageId: 'missingCleanup',
                  });
                }
              }
            }
            parent = parent.parent;
          }

          // Also check if using useRef
          const parentScope = context.getScope();
          const hasRef = parentScope.variables.some(
            v => v.name === 'wsRef' || v.name.includes('Ref')
          );

          if (!hasRef && !foundUseEffect) {
            context.report({
              node,
              messageId: 'useRefRecommended',
            });
          }
        }
      },
    };
  },
};

/**
 * Rule: Detect subscriptions without unsubscribe
 */
const noUncleanedSubscriptionsRule = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Ensure subscriptions are cleaned up',
      category: 'Best Practices',
      recommended: 'error',
    },
    messages: {
      missingCleanup: 'Potential memory leak: Subscription created without cleanup. Use: return () => subscription.unsubscribe();',
    },
    schema: [],
  },
  create(context) {
    return {
      CallExpression(node) {
        // Check for .subscribe() calls
        if (
          node.callee.type === 'MemberExpression' &&
          node.callee.property.name === 'subscribe'
        ) {
          // Find the parent useEffect
          let parent = node.parent;
          let foundUseEffect = false;

          while (parent && !foundUseEffect) {
            if (parent.type === 'CallExpression' &&
                parent.callee.type === 'Identifier' &&
                parent.callee.name === 'useEffect') {
              foundUseEffect = true;

              // Check if useEffect has a return statement with unsubscribe()
              const useEffectArg = parent.arguments[0];
              if (useEffectArg && useEffectArg.type === 'ArrowFunctionExpression') {
                const hasCleanup = useEffectArg.body.body?.some(
                  stmt =>
                    stmt.type === 'ReturnStatement' &&
                    context.getSourceCode().getText(stmt).includes('.unsubscribe()')
                );

                if (!hasCleanup) {
                  context.report({
                    node,
                    messageId: 'missingCleanup',
                  });
                }
              }
            }
            parent = parent.parent;
          }
        }
      },
    };
  },
};

/**
 * Export plugin in ESLint flat config format
 */
export default {
  meta: {
    name: 'eslint-plugin-memory-leak',
    version: '1.0.0',
  },
  rules: {
    'no-uncleaned-timers': noUncleanedTimersRule,
    'no-uncleaned-event-listeners': noUncleanedEventListenersRule,
    'no-uncleaned-websockets': noUncleanedWebsocketsRule,
    'no-uncleaned-subscriptions': noUncleanedSubscriptionsRule,
  },
};
