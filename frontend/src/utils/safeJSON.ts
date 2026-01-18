/**
 * Safe JSON parsing utility
 * Prevents app crashes from invalid JSON in localStorage or API responses
 */

/**
 * Safely parse JSON string with fallback value
 * @param json - JSON string to parse (can be null or undefined)
 * @param fallback - Default value to return if parsing fails
 * @returns Parsed object or fallback value
 *
 * @example
 * const user = safeJSONParse(localStorage.getItem('user'), null)
 * const events = safeJSONParse(localStorage.getItem('events'), [])
 * const config = safeJSONParse(localStorage.getItem('config'), {})
 */
export function safeJSONParse<T>(json: string | null | undefined, fallback: T): T {
  // Handle null/undefined input
  if (json === null || json === undefined) {
    return fallback;
  }

  // Handle empty string
  if (json.trim() === '') {
    return fallback;
  }

  try {
    return JSON.parse(json) as T;
  } catch (error) {
    // Log error for debugging but don't crash
    console.warn('Failed to parse JSON, using fallback value:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      jsonLength: json.length,
    });

    return fallback;
  }
}

/**
 * Safely stringify object to JSON
 * @param obj - Object to stringify
 * @param fallback - Fallback string if stringification fails
 * @returns JSON string or fallback value
 *
 * @example
 * const data = safeJSONStringify(complexObject, '{}')
 */
export function safeJSONStringify(obj: unknown, fallback: string = '{}'): string {
  try {
    return JSON.stringify(obj);
  } catch (error) {
    console.warn('Failed to stringify JSON, using fallback:', {
      error: error instanceof Error ? error.message : 'Unknown error',
    });

    return fallback;
  }
}

/**
 * Safely parse JSON with custom error handler
 * @param json - JSON string to parse
 * @param fallback - Default value if parsing fails
 * @param onError - Custom error handler
 * @returns Parsed object or fallback value
 */
export function safeJSONParseWithHandler<T>(
  json: string | null | undefined,
  fallback: T,
  onError: (error: Error) => void
): T {
  if (json === null || json === undefined || json.trim() === '') {
    return fallback;
  }

  try {
    return JSON.parse(json) as T;
  } catch (error) {
    const err = error instanceof Error ? error : new Error('Unknown JSON parse error');
    onError(err);
    return fallback;
  }
}

/**
 * Type guard to check if value is valid JSON string
 */
export function isValidJSONString(value: unknown): value is string {
  if (typeof value !== 'string') {
    return false;
  }

  if (value.trim() === '') {
    return false;
  }

  try {
    JSON.parse(value);
    return true;
  } catch {
    return false;
  }
}

/**
 * Safely get and parse item from localStorage
 * @param key - localStorage key
 * @param fallback - Fallback value if key doesn't exist or parsing fails
 * @returns Parsed value or fallback
 *
 * @example
 * const user = safeGetLocalStorage('user', null)
 * const settings = safeGetLocalStorage('settings', {})
 */
export function safeGetLocalStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') {
    return fallback;
  }

  try {
    const item = localStorage.getItem(key);
    return safeJSONParse(item, fallback);
  } catch (error) {
    console.warn(`Failed to get localStorage key "${key}":`, error);
    return fallback;
  }
}

/**
 * Safely stringify and set item in localStorage
 * @param key - localStorage key
 * @param value - Value to store
 * @returns true if successful, false otherwise
 */
export function safeSetLocalStorage(key: string, value: unknown): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  try {
    const jsonString = safeJSONStringify(value);
    localStorage.setItem(key, jsonString);
    return true;
  } catch (error) {
    console.warn(`Failed to set localStorage key "${key}":`, error);
    return false;
  }
}
