/**
 * Context Assembly Service for Secure Data Handling (TypeScript)
 *
 * Provides data minimization, PII redaction, and audit logging for AI systems.
 *
 * @author PsychSync Security Team
 * @version 1.0.0
 */

/**
 * Data access scopes based on user role
 */
export enum DataScope {
  PUBLIC = 'public',           // Non-sensitive data only
  RESTRICTED = 'restricted',   // Partial data (masked)
  CONFIDENTIAL = 'confidential', // Full data access
  ADMIN = 'admin',             // All data including secrets
}

/**
 * PII redaction levels
 */
export enum RedactionLevel {
  NONE = 'none',              // No redaction
  MINIMAL = 'minimal',        // Mask sensitive fields only
  MODERATE = 'moderate',      // Mask + anonymize PII
  AGGRESSIVE = 'aggressive',  // Maximum redaction
}

/**
 * Audit trail for data access and transformations
 */
export interface DataLineage {
  timestamp: string;
  userId: string;
  userRole: string;
  operation: string;
  dataScope: DataScope;
  redactionLevel: RedactionLevel;
  fieldsAccessed: string[];
  fieldsRedacted: string[];
  piiDetected: string[];
  secretsDetected: string[];
  inputHash: string;
  outputHash: string;
  processingTimeMs: number;
}

/**
 * Result of context assembly operation
 */
export interface ContextAssemblyResult {
  assembledContext: Record<string, any>;
  lineage: DataLineage;
  warnings: string[];
  metadata: Record<string, any>;
}

/**
 * Detect and classify PII in text data
 */
export class PIIDetector {
  private static readonly PATTERNS: Record<string, RegExp> = {
    email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi,
    phoneUs: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,
    phoneIntl: /\b\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b/g,
    ssn: /\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/g,
    creditCard: /\b(?:\d[ -]*?){13,16}\b/g,
    ipAddress: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g,
    apiKey: /\b[A-Za-z0-9]{32,}\b/g,
    awsKey: /\bAKIA[0-9A-Z]{16}\b/g,
    githubToken: /\bghp_[A-Za-z0-9]{36}\b/g,
    bearerToken: /\bBearer [A-Za-z0-9\-._~+/]+=*\b/gi,
  };

  /**
   * Detect PII in text
   */
  detectPII(text: string): Record<string, string[]> {
    const detections: Record<string, string[]> = {};

    for (const [piiType, pattern] of Object.entries(PIIDetector.PATTERNS)) {
      const matches = text.match(pattern);
      if (matches) {
        detections[piiType] = matches;
      }
    }

    return detections;
  }

  /**
   * Check if text contains any PII
   */
  hasPII(text: string): boolean {
    const detections = this.detectPII(text);
    return Object.keys(detections).length > 0;
  }
}

/**
 * Detect and redact secrets and sensitive credentials
 */
export class SecretDetector {
  private static readonly SECRET_PATTERNS: Record<string, RegExp> = {
    password: /(?i)(?:password|passwd|pwd)\s*[=:]\s*[^\s'"<>]+/g,
    apiKey: /(?i)(?:api[_-]?key|apikey)\s*[=:]\s*[^\s'"<>]+/g,
    secretKey: /(?i)(?:secret[_-]?key|secretkey)\s*[=:]\s*[^\s'"<>]+/g,
    token: /(?i)(?:token|auth[_-]?token)\s*[=:]\s*[^\s'"<>]+/g,
    connectionString: /(?i)(?:mongodb|mysql|postgres|redis):\/\/[^\s'"<>]+/g,
    jwt: /\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g,
    privateKey: /-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----/g,
    awsAccessKey: /\bAKIA[0-9A-Z]{16}\b/g,
    azureKey: /\b[A-Za-z0-9/+=]{88}\b/g,
  };

  /**
   * Detect secrets in text
   */
  detectSecrets(text: string): Record<string, string[]> {
    const detections: Record<string, string[]> = {};

    for (const [secretType, pattern] of Object.entries(SecretDetector.SECRET_PATTERNS)) {
      const matches = text.match(pattern);
      if (matches) {
        detections[secretType] = matches.map(m => this.redactMatch(m));
      }
    }

    return detections;
  }

  /**
   * Check if text contains any secrets
   */
  hasSecrets(text: string): boolean {
    const detections = this.detectSecrets(text);
    return Object.keys(detections).length > 0;
  }

  private redactMatch(match: string): string {
    if (match.length > 20) {
      return `${match.substring(0, 8)}...${match.substring(match.length - 4)}`;
    }
    return '*'.repeat(match.length);
  }
}

/**
 * Redact or anonymize PII in text
 */
export class PIIRedactor {
  /**
   * Redact email address (show domain)
   */
  redactEmail(email: string): string {
    const pattern = /\b([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,}))\b/gi;
    return email.replace(pattern, '$1***@$2$3');
  }

  /**
   * Redact phone number (show last 4 digits)
   */
  redactPhone(phone: string): string {
    // US format
    const usPattern = /\b\d{3}[-.]?\d{3}[-.]?(\d{4})\b/g;
    if (usPattern.test(phone)) {
      return phone.replace(usPattern, '***-***-$1');
    }

    // International format
    const intlPattern = /\b(\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?)\d{1,4}[-.\s]?(\d{1,4})\b/g;
    const matches = phone.match(intlPattern);
    if (matches) {
      return phone.replace(intlPattern, '$1***');
    }

    return phone;
  }

  /**
   * Redact SSN completely
   */
  redactSSN(ssn: string): string {
    return ssn.replace(/\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/g, '***-**-****');
  }

  /**
   * Redact credit card (show last 4 digits)
   */
  redactCreditCard(card: string): string {
    return card.replace(/\b(\d{4}[-.\s]?){3}(\d{4})\b/g, '****-****-****-$2');
  }

  /**
   * Redact all PII in text based on level
   */
  redactText(text: string, level: RedactionLevel = RedactionLevel.MODERATE): string {
    if (level === RedactionLevel.NONE) {
      return text;
    }

    let redacted = text;

    // Always redact SSNs and credit cards
    redacted = this.redactSSN(redacted);
    redacted = this.redactCreditCard(redacted);

    if (level === RedactionLevel.MODERATE || level === RedactionLevel.AGGRESSIVE) {
      // Redact emails and phones
      redacted = this.redactEmail(redacted);
      redacted = this.redactPhone(redacted);
    }

    if (level === RedactionLevel.AGGRESSIVE) {
      // Additional redactions (IP addresses, etc.)
      redacted = redacted.replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '***.***.***.***');
    }

    return redacted;
  }
}

/**
 * Hash sensitive identifiers for privacy
 */
export class IDHasher {
  private salt: string;

  constructor(salt?: string) {
    // Use Web Crypto API for Node.js, or a simple implementation for browser
    this.salt = salt || this.generateSalt();
  }

  private generateSalt(): string {
    const timestamp = Date.now().toString();
    let hash = 0;
    for (let i = 0; i < timestamp.length; i++) {
      const char = timestamp.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16).padStart(16, '0').substring(0, 16);
  }

  /**
   * Hash an identifier (simple implementation)
   */
  async hashId(identifier: string): Promise<string> {
    const input = this.salt + identifier;
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16);
  }

  /**
   * Hash specific ID fields in data
   */
  async hashIdsInData(data: Record<string, any>, idFields: Set<string>): Promise<Record<string, any>> {
    const result = { ...data };

    for (const field of idFields) {
      if (field in result && typeof result[field] === 'string') {
        result[field] = await this.hashId(result[field]);
      }
    }

    return result;
  }
}

/**
 * Role-based data retrieval with automatic scoping
 */
export class RoleScopedRetrieval {
  private static readonly ROLE_TO_SCOPE: Record<string, DataScope> = {
    user: DataScope.RESTRICTED,
    premium_user: DataScope.CONFIDENTIAL,
    admin: DataScope.ADMIN,
    analyst: DataScope.CONFIDENTIAL,
    viewer: DataScope.PUBLIC,
    superadmin: DataScope.ADMIN,
  };

  /**
   * Get data access scope for role
   */
  getScopeForRole(role: string): DataScope {
    return RoleScopedRetrieval.ROLE_TO_SCOPE[role.toLowerCase()] || DataScope.PUBLIC;
  }

  /**
   * Filter data based on user role
   */
  filterByRole(data: Record<string, any>, role: string): Record<string, any> {
    const scope = this.getScopeForRole(role);
    return this.minimizeData(data, scope);
  }

  private minimizeData(data: Record<string, any>, scope: DataScope): Record<string, any> {
    if (scope === DataScope.ADMIN) {
      return { ...data };
    }

    if (scope === DataScope.CONFIDENTIAL) {
      return Object.fromEntries(
        Object.entries(data).filter(([key]) => !this.isSecretField(key))
      );
    }

    if (scope === DataScope.RESTRICTED) {
      return this.maskSensitiveFields(data);
    }

    if (scope === DataScope.PUBLIC) {
      return Object.fromEntries(
        Object.entries(data).filter(([key]) => this.isPublicField(key))
      );
    }

    return {};
  }

  private isSecretField(fieldName: string): boolean {
    const secretKeywords = ['password', 'secret', 'token', 'key', 'auth'];
    const lowerName = fieldName.toLowerCase();
    return secretKeywords.some(keyword => lowerName.includes(keyword));
  }

  private isPublicField(fieldName: string): boolean {
    const sensitiveKeywords = [
      'email', 'phone', 'ssn', 'social', 'credit', 'card',
      'password', 'secret', 'token', 'address', 'location'
    ];
    const lowerName = fieldName.toLowerCase();
    return !sensitiveKeywords.some(keyword => lowerName.includes(keyword));
  }

  private maskSensitiveFields(data: Record<string, any>): Record<string, any> {
    const masked: Record<string, any> = {};

    for (const [key, value] of Object.entries(data)) {
      if (this.isSecretField(key)) {
        masked[key] = '***REDACTED***';
      } else if (typeof value === 'string') {
        masked[key] = this.maskPIIPartial(key, value);
      } else {
        masked[key] = value;
      }
    }

    return masked;
  }

  private maskPIIPartial(fieldName: string, value: string): string {
    const lowerName = fieldName.toLowerCase();

    if (lowerName.includes('email')) {
      const parts = value.split('@');
      if (parts.length === 2) {
        return `${parts[0].substring(0, 2)}***@${parts[1]}`;
      }
    } else if (lowerName.includes('phone')) {
      const digits = value.replace(/\D/g, '');
      if (digits.length >= 4) {
        return `***-***-${digits.substring(digits.length - 4)}`;
      }
    } else if (lowerName.includes('name')) {
      const parts = value.split(' ');
      if (parts.length > 0) {
        return `${parts[0][0]}.`;
      }
    }

    return value;
  }
}

/**
 * Main service for assembling secure context for AI systems
 */
export class ContextAssemblyService {
  private piiDetector: PIIDetector;
  private secretDetector: SecretDetector;
  private redactor: PIIRedactor;
  private hasher: IDHasher;
  private roleRetrieval: RoleScopedRetrieval;
  private enableAuditLogging: boolean;

  constructor(options: {
    enableAuditLogging?: boolean;
  } = {}) {
    this.piiDetector = new PIIDetector();
    this.secretDetector = new SecretDetector();
    this.redactor = new PIIRedactor();
    this.hasher = new IDHasher();
    this.roleRetrieval = new RoleScopedRetrieval();
    this.enableAuditLogging = options.enableAuditLogging ?? true;
  }

  /**
   * Assemble secure context for AI processing
   */
  async assembleContext(params: {
    data: Record<string, any>;
    userId: string;
    userRole: string;
    redactionLevel?: RedactionLevel;
    idFields?: Set<string>;
  }): Promise<ContextAssemblyResult> {
    const {
      data,
      userId,
      userRole,
      redactionLevel = RedactionLevel.MODERATE,
      idFields,
    } = params;

    const startTime = Date.now();
    const startTimeIso = new Date().toISOString();

    // Calculate input hash
    const inputHash = this.calculateHash(data);

    // Initialize lineage
    const lineage: DataLineage = {
      timestamp: startTimeIso,
      userId,
      userRole,
      operation: 'assemble_context',
      dataScope: this.roleRetrieval.getScopeForRole(userRole),
      redactionLevel,
      fieldsAccessed: [],
      fieldsRedacted: [],
      piiDetected: [],
      secretsDetected: [],
      inputHash,
      outputHash: '',
      processingTimeMs: 0,
    };

    const warnings: string[] = [];
    const metadata: Record<string, any> = {};

    // Step 1: Role-based filtering
    const filteredData = this.roleRetrieval.filterByRole(data, userRole);
    lineage.fieldsAccessed = Object.keys(filteredData);

    // Step 2: Hash sensitive IDs
    let processedData = filteredData;
    if (idFields) {
      processedData = await this.hasher.hashIdsInData(processedData, idFields);
    }

    // Step 3: Detect PII and secrets
    const textData = this.dictToText(processedData);
    const piiDetections = this.piiDetector.detectPII(textData);
    if (Object.keys(piiDetections).length > 0) {
      lineage.piiDetected = Object.keys(piiDetections);
      warnings.push(`PII detected: ${lineage.piiDetected.join(', ')}`);
    }

    const secretDetections = this.secretDetector.detectSecrets(textData);
    if (Object.keys(secretDetections).length > 0) {
      lineage.secretsDetected = Object.keys(secretDetections);
      warnings.push(`Secrets detected and redacted: ${lineage.secretsDetected.join(', ')}`);
    }

    // Step 4: Redact PII and secrets
    const assembledContext = this.redactData(processedData, redactionLevel);
    lineage.fieldsRedacted = Object.keys(data).filter(key => !(key in assembledContext));

    // Add metadata
    metadata.assembledAt = startTimeIso;
    metadata.userRole = userRole;
    metadata.dataScope = lineage.dataScope;
    metadata.redactionLevel = redactionLevel;
    metadata.originalFieldCount = Object.keys(data).length;
    metadata.assembledFieldCount = Object.keys(assembledContext).length;
    metadata.fieldsRedacted = lineage.fieldsRedacted.length;

    // Calculate output hash and processing time
    const outputHash = this.calculateHash(assembledContext);
    const processingTime = Date.now() - startTime;

    lineage.outputHash = outputHash;
    lineage.processingTimeMs = processingTime;

    const result: ContextAssemblyResult = {
      assembledContext,
      lineage,
      warnings,
      metadata,
    };

    // Audit log
    if (this.enableAuditLogging) {
      this.logAudit(result);
    }

    return result;
  }

  /**
   * Assemble secure context for RAG (Retrieval-Augmented Generation)
   */
  async assembleRAGContext(params: {
    query: string;
    documents: Record<string, any>[];
    userId: string;
    userRole: string;
    redactionLevel?: RedactionLevel;
  }): Promise<ContextAssemblyResult> {
    const { query, documents, userId, userRole, redactionLevel = RedactionLevel.MODERATE } = params;

    const data = {
      query,
      documents,
      documentCount: documents.length,
    };

    const result = await this.assembleContext({
      data,
      userId,
      userRole,
      redactionLevel,
    });

    // Add RAG-specific metadata
    result.metadata.ragQuery = result.assembledContext.query;
    result.metadata.ragDocumentCount = result.assembledContext.documentCount;

    return result;
  }

  private redactData(data: Record<string, any>, level: RedactionLevel): Record<string, any> {
    const redacted: Record<string, any> = {};

    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'string') {
        // Detect and redact secrets first
        if (this.secretDetector.hasSecrets(value)) {
          redacted[key] = '***SECRET_REDACTED***';
        } else {
          // Redact PII
          redacted[key] = this.redactor.redactText(value, level);
        }
      } else if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value)) {
          redacted[key] = value.map(item =>
            typeof item === 'object' && item !== null
              ? this.redactData(item, level)
              : item
          );
        } else {
          redacted[key] = this.redactData(value, level);
        }
      } else {
        redacted[key] = value;
      }
    }

    return redacted;
  }

  private dictToText(data: Record<string, any>): string {
    return JSON.stringify(data);
  }

  private calculateHash(data: any): string {
    const str = JSON.stringify(data, Object.keys(data).sort());
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16).substring(0, 16);
  }

  private logAudit(result: ContextAssemblyResult): void {
    const auditInfo = {
      timestamp: result.lineage.timestamp,
      userId: result.lineage.userId,
      role: result.lineage.userRole,
      operation: result.lineage.operation,
      scope: result.lineage.dataScope,
      redactionLevel: result.lineage.redactionLevel,
      fieldsAccessed: result.lineage.fieldsAccessed.length,
      fieldsRedacted: result.lineage.fieldsRedacted.length,
      piiDetected: result.lineage.piiDetected,
      secretsDetected: result.lineage.secretsDetected,
      processingTimeMs: result.lineage.processingTimeMs,
      inputHash: result.lineage.inputHash,
      outputHash: result.lineage.outputHash,
    };

    console.log('[Context Assembly Audit]', JSON.stringify(auditInfo));
  }
}

// Convenience functions
export async function assembleSecureContext(
  data: Record<string, any>,
  userId: string,
  userRole: string,
  redactionLevel?: RedactionLevel
): Promise<ContextAssemblyResult> {
  const service = new ContextAssemblyService();
  return service.assembleContext({ data, userId, userRole, redactionLevel });
}

export function redactPIIInText(text: string, level?: RedactionLevel): string {
  const redactor = new PIIRedactor();
  return redactor.redactText(text, level);
}

export default ContextAssemblyService;
