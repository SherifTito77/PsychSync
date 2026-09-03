/**
 * Polyfills for Cross-Browser Compatibility
 *
 * This file imports polyfills needed for broader browser support.
 * Currently targets modern browsers as defined in package.json browserslist:
 * - last 2 versions
 * - >= 1%
 * - not dead
 * - not IE 11
 *
 * For older browser support (IE11, Safari < 12, etc.), install core-js:
 *   npm install core-js regenerator-runtime
 *
 * Then uncomment the imports below:
 */

// Uncomment for broader browser support:
// import 'core-js/stable';
// import 'regenerator-runtime/runtime';

/**
 * Feature Detection Polyfills
 *
 * These polyfills provide graceful degradation for browsers
 * that don't support certain APIs.
 */

// IntersectionObserver polyfill for older browsers
if (!('IntersectionObserver' in window)) {
  // Load from CDN when needed
  console.warn('IntersectionObserver not supported. Consider adding polyfill.');
}

// ResizeObserver polyfill for older browsers
if (!('ResizeObserver' in window)) {
  console.warn('ResizeObserver not supported. Consider adding polyfill.');
}

// Smooth scroll polyfill for older Safari
if (!('scrollBehavior' in document.documentElement.style)) {
  document.documentElement.style.scrollBehavior = 'auto';
  console.info('Smooth scroll not supported. Using standard scroll.');
}

/**
 * String.prototype.replaceAll() polyfill
 * Added in: Chrome 85, Edge 85, Firefox 77, Safari 13.1
 */
if (!String.prototype.replaceAll) {
  String.prototype.replaceAll = function(search: string | RegExp, replacement: string): string {
    const str = String(this);
    if (search instanceof RegExp) {
      return str.replace(search, replacement);
    }
    return str.replace(new RegExp(search, 'g'), replacement);
  };
}

/**
 * Array.prototype.at() polyfill
 * Added in: Chrome 92, Edge 92, Firefox 90, Safari 15.4
 */
if (!Array.prototype.at) {
  Array.prototype.at = function(index: number) {
    const len = this.length;
    const relativeIndex = index >= 0 ? index : len + index;
    return relativeIndex >= 0 && relativeIndex < len ? this[relativeIndex] : undefined;
  };
}

/**
 * Object.hasOwn() polyfill
 * Added in: Chrome 93, Edge 93, Firefox 92, Safari 15.4
 */
if (!Object.hasOwn) {
  Object.hasOwn = function(obj: object, prop: PropertyKey): boolean {
    return Object.prototype.hasOwnProperty.call(obj, prop);
  };
}

/**
 * Promise.withResolvers() polyfill
 * Added in: Chrome 119, Edge 119, Firefox 121
 */
if (!('withResolvers' in Promise)) {
  (Promise as any).withResolvers = function() {
    let resolve: (value: unknown) => void;
    let reject: (reason?: unknown) => void;
    const promise = new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve, reject };
  };
}

export {};
