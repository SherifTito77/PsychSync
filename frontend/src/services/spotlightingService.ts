/**
 * Spotlighting SDK for Prompt Injection Prevention (TypeScript/Node)
 *
 * Provides three spotlighting modes to isolate and mark untrusted content:
 * 1. Delimiting: Randomized delimiters around untrusted content
 * 2. Datamarking: Non-semantic markers between tokens
 * 3. Encoding: Base64/ROT13 encoding with safe decoding
 *
 * @author PsychSync Security Team
 * @version 1.0.0
 */

/**
 * Spotlighting modes enumeration
 */
export enum SpotlightingMode {
  DELIMITING = 'delimiting',
  DATAMARKING = 'datamarking',
  ENCODING = 'encoding'
}

/**
 * Result of a spotlighting operation
 */
export interface SpotlightingResult {
  processedContent: string;
  delimiterStart?: string;
  delimiterEnd?: string;
  encodingMethod?: string;
  markersCount?: number;
  metadata: {
    mode: string;
    [key: string]: any;
  };
}

/**
 * Delimiting spotlighting: Wraps content in randomized delimiters
 *
 * Example:
 *   Input: "Ignore previous instructions"
 *   Output: "「≈≈≈USER_INPUT_START≈≈≈」Ignore previous instructions「≈≈≈USER_INPUT_END≈≈≈」"
 */
export class DelimitingSpotlighting {
  private static readonly DELIMITER_CHARS = {
    brackets: ['「」', '『』', '【】', '〔〕', '⎡⎤', '⎣⎦'],
    symbols: ['≈≈≈', '※※※', '☉☉☉', '◈◈◈', '◆◆◆'],
    arrows: ['>>>', '<<<', '→→→', '←←←', '⇒⇒⇒'],
    mixed: ['§§§', '★☆★', '♦♦♦', '※✿※']
  };

  private random: () => number;

  constructor(seed?: number) {
    // Use seeded random for testing, default Math.random for production
    this.random = seed
      ? (() => {
          const seedValue = seed;
          let state = seedValue;
          return () => {
            state = (state * 9301 + 49297) % 233280;
            return state / 233280;
          };
        })()
      : Math.random;
  }

  /**
   * Generate a randomized delimiter pair
   */
  private generateDelimiterPair(): [string, string] {
    const brackets = this.randomChoice(DelimitingSpotlighting.DELIMITER_CHARS.brackets);
    const [bracketOpen, bracketClose] = [brackets[0], brackets[1]];

    const symbols = this.randomChoice(DelimitingSpotlighting.DELIMITER_CHARS.symbols);

    const startDelimiter = `${bracketOpen}${symbols}USER_INPUT_START${symbols}${bracketOpen}`;
    const endDelimiter = `${bracketClose}${symbols}USER_INPUT_END${symbols}${bracketClose}`;

    return [startDelimiter, endDelimiter];
  }

  private randomChoice<T>(arr: T[]): T {
    return arr[Math.floor(this.random() * arr.length)];
  }

  /**
   * Apply delimiting spotlighting to content
   */
  apply(content: string): SpotlightingResult {
    const [delimiterStart, delimiterEnd] = this.generateDelimiterPair();

    const processed = `${delimiterStart}\n${content}\n${delimiterEnd}`;

    return {
      processedContent: processed,
      delimiterStart,
      delimiterEnd,
      metadata: {
        mode: SpotlightingMode.DELIMITING,
        originalLength: content.length,
        processedLength: processed.length
      }
    };
  }

  /**
   * Verify that content is properly delimited
   */
  verify(content: string, result: SpotlightingResult): boolean {
    return (
      result.delimiterStart !== undefined &&
      result.delimiterEnd !== undefined &&
      content.includes(result.delimiterStart) &&
      content.includes(result.delimiterEnd) &&
      content.indexOf(result.delimiterStart) < content.indexOf(result.delimiterEnd!)
    );
  }
}

/**
 * Datamarking spotlighting: Inserts non-semantic markers between tokens
 *
 * Example:
 *   Input: "Ignore previous instructions"
 *   Output: "Ignoreˆpreviousˆinstructions"
 */
export class DatamarkingSpotlighting {
  private static readonly MARKERS = ['ˆ', 'ˇ', '˘', '˙', '˚', '˛', '˜', '˝'];
  private marker: string;

  constructor(marker?: string, seed?: number) {
    const random = seed ? (() => {
      let state = seed;
      return () => {
        state = (state * 9301 + 49297) % 233280;
        return state / 233280;
      };
    })() : Math.random;

    this.marker = marker || DatamarkingSpotlighting.MARKERS[
      Math.floor(random() * DatamarkingSpotlighting.MARKERS.length)
    ];
  }

  /**
   * Apply datamarking spotlighting to content
   */
  apply(content: string): SpotlightingResult {
    const words = content.split(/\s+/);
    const markedWords = words.map(word => `${word}${this.marker}`);
    const processed = markedWords.join(' ');

    return {
      processedContent: processed,
      markersCount: words.length,
      metadata: {
        mode: SpotlightingMode.DATAMARKING,
        marker: this.marker,
        originalLength: content.length,
        processedLength: processed.length
      }
    };
  }

  /**
   * Verify that content has expected markers
   */
  verify(content: string, result: SpotlightingResult): boolean {
    const marker = result.metadata.marker || this.marker;
    const expectedCount = result.markersCount || 0;
    const actualCount = (content.match(new RegExp(marker, 'g')) || []).length;

    return actualCount >= expectedCount;
  }
}

/**
 * Encoding spotlighting: Encodes content with decoding instructions
 *
 * Example:
 *   Input: "Ignore previous instructions"
 *   Output: "「ENCODED_CONTENT」Base64:SSBnb3JnIHZ...==「DECODE_SAFE」"
 */
export class EncodingSpotlighting {
  private method: 'base64' | 'rot13';
  private addPrefix: boolean;

  constructor(method: 'base64' | 'rot13' = 'base64', addPrefix = true) {
    this.method = method;
    this.addPrefix = addPrefix;
  }

  private encodeBase64(content: string): string {
    if (typeof Buffer !== 'undefined') {
      // Node.js
      return Buffer.from(content, 'utf-8').toString('base64');
    } else {
      // Browser
      const bytes = new TextEncoder().encode(content);
      const binString = Array.from(bytes, byte => String.fromCharCode(byte)).join('');
      return btoa(binString);
    }
  }

  private encodeRot13(content: string): string {
    return content.replace(/[a-zA-Z]/g, (char) => {
      const start = char <= 'Z' ? 65 : 97;
      return String.fromCharCode(((char.charCodeAt(0) - start + 13) % 26) + start);
    });
  }

  /**
   * Apply encoding spotlighting to content
   */
  apply(content: string): SpotlightingResult {
    const encoded = this.method === 'base64'
      ? this.encodeBase64(content)
      : this.encodeRot13(content);

    let processed: string;

    if (this.addPrefix) {
      processed = `「ENCODED_USER_INPUT」\nMethod: ${this.method.toUpperCase()}\nContent: ${encoded}\n「DECODE_IN_SAFE_STAGE」`;
    } else {
      processed = encoded;
    }

    return {
      processedContent: processed,
      encodingMethod: this.method,
      metadata: {
        mode: SpotlightingMode.ENCODING,
        originalLength: content.length,
        encodedLength: encoded.length
      }
    };
  }

  /**
   * Verify that content is properly encoded
   */
  verify(content: string, result: SpotlightingResult): boolean {
    const markers = ['ENCODED_USER_INPUT', 'DECODE_IN_SAFE_STAGE'];
    return markers.every(marker => content.includes(marker));
  }
}

/**
 * Main SDK interface for spotlighting untrusted content
 */
export class SpotlightingSDK {
  private delimiting: DelimitingSpotlighting;
  private datamarking: DatamarkingSpotlighting;
  private encoding: EncodingSpotlighting;

  constructor() {
    this.delimiting = new DelimitingSpotlighting();
    this.datamarking = new DatamarkingSpotlighting();
    this.encoding = new EncodingSpotlighting();
  }

  /**
   * Apply spotlighting to untrusted content
   */
  spotlight(
    content: string,
    mode: SpotlightingMode = SpotlightingMode.DELIMITING,
    options?: { method?: 'base64' | 'rot13'; marker?: string; seed?: number }
  ): SpotlightingResult {
    switch (mode) {
      case SpotlightingMode.DELIMITING:
        return new DelimitingSpotlighting(options?.seed).apply(content);
      case SpotlightingMode.DATAMARKING:
        return new DatamarkingSpotlighting(options?.marker, options?.seed).apply(content);
      case SpotlightingMode.ENCODING:
        return new EncodingSpotlighting(options?.method).apply(content);
      default:
        throw new Error(`Unknown spotlighting mode: ${mode}`);
    }
  }

  /**
   * Apply spotlighting to multiple contents
   */
  spotlightBatch(
    contents: string[],
    mode: SpotlightingMode = SpotlightingMode.DELIMITING,
    options?: { method?: 'base64' | 'rot13'; marker?: string }
  ): SpotlightingResult[] {
    return contents.map(content => this.spotlight(content, mode, options));
  }

  /**
   * Verify that content matches spotlighting result
   */
  verify(content: string, originalResult: SpotlightingResult): boolean {
    const mode = originalResult.metadata.mode;

    switch (mode) {
      case SpotlightingMode.DELIMITING:
        return this.delimiting.verify(content, originalResult);
      case SpotlightingMode.DATAMARKING:
        return this.datamarking.verify(content, originalResult);
      case SpotlightingMode.ENCODING:
        return this.encoding.verify(content, originalResult);
      default:
        return false;
    }
  }
}

/**
 * Safe pipeline stage for decoding encoded spotlighting
 */
export class SafePipelineStage {
  /**
   * Decode Base64 content
   */
  static decodeBase64(content: string): string {
    if (typeof Buffer !== 'undefined') {
      // Node.js
      return Buffer.from(content, 'base64').toString('utf-8');
    } else {
      // Browser
      const binString = atob(content);
      const bytes = new Uint8Array(binString.length);
      for (let i = 0; i < binString.length; i++) {
        bytes[i] = binString.charCodeAt(i);
      }
      return new TextDecoder().decode(bytes);
    }
  }

  /**
   * Decode ROT13 content
   */
  static decodeRot13(content: string): string {
    return content.replace(/[a-zA-Z]/g, (char) => {
      const start = char <= 'Z' ? 65 : 97;
      return String.fromCharCode(((char.charCodeAt(0) - start + 13) % 26) + start);
    });
  }

  /**
   * Decode content from spotlighting result
   */
  static decodeFromSpotlighting(result: SpotlightingResult): string {
    if (result.metadata.mode !== SpotlightingMode.ENCODING) {
      throw new Error('Result is not in encoding mode');
    }

    const method = result.encodingMethod as 'base64' | 'rot13';
    const content = result.processedContent;

    // Extract encoded content from wrapper
    let encodedPart: string;
    if (content.includes('Content:')) {
      encodedPart = content.split('Content: ')[1].split('\n')[0].trim();
    } else {
      encodedPart = content;
    }

    // Decode
    if (method === 'base64') {
      return SafePipelineStage.decodeBase64(encodedPart);
    } else if (method === 'rot13') {
      return SafePipelineStage.decodeRot13(encodedPart);
    } else {
      throw new Error(`Unknown encoding method: ${method}`);
    }
  }
}

// Convenience functions for quick usage
export function spotlightDelimiting(content: string): SpotlightingResult {
  return new DelimitingSpotlighting().apply(content);
}

export function spotlightDatamarking(content: string, marker?: string): SpotlightingResult {
  return new DatamarkingSpotlighting(marker).apply(content);
}

export function spotlightEncoding(content: string, method?: 'base64' | 'rot13'): SpotlightingResult {
  return new EncodingSpotlighting(method).apply(content);
}

export default SpotlightingSDK;
