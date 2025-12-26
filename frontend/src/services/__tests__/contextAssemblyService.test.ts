/**
 * Unit Tests for Context Assembly Service (TypeScript)
 * Demonstrates PII redaction, secret detection, and data lineage tracking.
 *
 * Run: npm test contextAssemblyService.test.ts
 */

import {
  ContextAssemblyService,
  DataScope,
  PIIDetector,
  PIIRedactor,
  SecretDetector,
  IDHasher,
  RoleScopedRetrieval,
  RedactionLevel,
  assembleSecureContext,
  redactPIIInText,
  type ContextAssemblyResult,
  type DataLineage,
} from '../contextAssemblyService';

// =============================================================================
// Test Data
// =============================================================================

const TEST_DATA_WITH_PII = {
  name: 'John Doe',
  email: 'john.doe@example.com',
  phone: '555-123-4567',
  ssn: '123-45-6789',
  address: '123 Main St, City, State 12345',
  creditCard: '4532-1234-5678-9010',
  notes: 'Regular user',
};

const TEST_DATA_WITH_SECRETS = {
  username: 'testuser',
  password: 'SecretPassword123!',
  apiKey: 'AKIAIOSFODNN7EXAMPLE',
  databaseUrl: 'mongodb://user:pass123@localhost:27017/db',
  jwtToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example',
  notes: 'Configuration data',
};

const RAG_QUERY_WITH_PII = "What is John Doe's email address and phone number?";

const RAG_DOCUMENTS = [
  {
    id: 'doc1',
    title: 'User Profile',
    content: 'Contact: John Doe, email: john@example.com, phone: 555-987-6543',
  },
  {
    id: 'doc2',
    title: 'Account Info',
    content: 'SSN: 987-65-4321, Credit Card: 5423-4567-8901-2345',
  },
];

// =============================================================================
// PII Detection Tests
// =============================================================================

describe('PIIDetector', () => {
  let detector: PIIDetector;

  beforeEach(() => {
    detector = new PIIDetector();
  });

  describe('Email Detection', () => {
    test('should detect email addresses', () => {
      const text = 'Contact us at john.doe@example.com for support';
      const detections = detector.detectPII(text);

      expect(detections.email).toBeDefined();
      expect(detections.email).toContain('john.doe@example.com');
    });

    test('should detect multiple emails', () => {
      const text = 'Email john@example.com or jane@test.com';
      const detections = detector.detectPII(text);

      expect(detections.email).toBeDefined();
      expect(detections.email.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Phone Detection', () => {
    test('should detect US phone numbers', () => {
      const text = 'Call me at 555-123-4567';
      const detections = detector.detectPII(text);

      expect(detections.phoneUs).toBeDefined();
    });

    test('should detect international phone numbers', () => {
      const text = 'International: +44 20 7123 4567';
      const detections = detector.detectPII(text);

      expect(detections.phoneIntl).toBeDefined();
    });
  });

  describe('SSN Detection', () => {
    test('should detect SSN', () => {
      const text = 'My SSN is 123-45-6789';
      const detections = detector.detectPII(text);

      expect(detections.ssn).toBeDefined();
    });
  });

  describe('Credit Card Detection', () => {
    test('should detect credit card numbers', () => {
      const text = 'Card: 4532-1234-5678-9010';
      const detections = detector.detectPII(text);

      expect(detections.creditCard).toBeDefined();
    });
  });

  describe('hasPII', () => {
    test('should return true when PII present', () => {
      const text = 'Email: john@example.com';
      expect(detector.hasPII(text)).toBe(true);
    });

    test('should return false when no PII', () => {
      const text = 'Just regular text with no personal info';
      expect(detector.hasPII(text)).toBe(false);
    });
  });
});

// =============================================================================
// Secret Detection Tests
// =============================================================================

describe('SecretDetector', () => {
  let detector: SecretDetector;

  beforeEach(() => {
    detector = new SecretDetector();
  });

  test('should detect passwords', () => {
    const text = 'password=SecretPassword123!';
    const detections = detector.detectSecrets(text);

    expect(detections.password).toBeDefined();
  });

  test('should detect AWS keys', () => {
    const text = 'AWS_KEY=AKIAIOSFODNN7EXAMPLE';
    const detections = detector.detectSecrets(text);

    expect(detections.awsAccessKey).toBeDefined();
  });

  test('should detect JWT tokens', () => {
    const text = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9';
    const detections = detector.detectSecrets(text);

    expect(detections.jwt).toBeDefined();
  });

  test('should redact detected secrets', () => {
    const text = 'password=MyVeryLongSecretPassword123!';
    const detections = detector.detectSecrets(text);

    // Should be redacted (not show full password)
    const passwordEntry = detections.password?.[0];
    expect(passwordEntry).not.toContain('MyVeryLongSecretPassword123!');
    expect(passwordEntry).toContain('...');
  });
});

// =============================================================================
// PII Redaction Tests
// =============================================================================

describe('PIIRedactor', () => {
  let redactor: PIIRedactor;

  beforeEach(() => {
    redactor = new PIIRedactor();
  });

  test('should redact email address', () => {
    const email = 'john.doe@example.com';
    const redacted = redactor.redactEmail(email);

    expect(redacted).toContain('***@');
    expect(redacted).toContain('example.com');
  });

  test('should redact phone number', () => {
    const phone = '555-123-4567';
    const redacted = redactor.redactPhone(phone);

    expect(redacted).toContain('***-***-');
    expect(redacted).toContain('4567');
  });

  test('should redact SSN', () => {
    const ssn = '123-45-6789';
    const redacted = redactor.redactSSN(ssn);

    expect(redacted).toBe('***-**-****');
  });

  test('should redact credit card', () => {
    const card = '4532-1234-5678-9010';
    const redacted = redactor.redactCreditCard(card);

    expect(redacted).toContain('****-****-****-');
    expect(redacted).toContain('9010');
  });

  test('should apply moderate redaction level', () => {
    const text = 'SSN: 123-45-6789, Email: john@example.com, Phone: 555-123-4567';
    const redacted = redactor.redactText(text, RedactionLevel.MODERATE);

    expect(redacted).toContain('***-**-****');  // SSN
    expect(redacted).toContain('***@');         // Email
    expect(redacted).toContain('***-***-');     // Phone
  });

  test('should apply aggressive redaction level', () => {
    const text = 'IP: 192.168.1.1, Email: john@example.com';
    const redacted = redactor.redactText(text, RedactionLevel.AGGRESSIVE);

    expect(redacted).toContain('***.***.***.***');  // IP
    expect(redacted).toContain('***@');              // Email
  });

  test('should not redact at NONE level', () => {
    const text = 'Email: john@example.com';
    const redacted = redactor.redactText(text, RedactionLevel.NONE);

    expect(redacted).toBe(text);
  });
});

// =============================================================================
// ID Hashing Tests
// =============================================================================

describe('IDHasher', () => {
  let hasher: IDHasher;

  beforeEach(() => {
    hasher = new IDHasher();
  });

  test('should hash IDs consistently', async () => {
    const id = 'user_12345';
    const hash1 = await hasher.hashId(id);
    const hash2 = await hasher.hashId(id);

    expect(hash1).toBe(hash2);
  });

  test('should produce different hashes for different IDs', async () => {
    const hash1 = await hasher.hashId('user_123');
    const hash2 = await hasher.hashId('user_456');

    expect(hash1).not.toBe(hash2);
  });

  test('should hash specific fields in data', async () => {
    const data = {
      userId: 'user_123',
      name: 'John',
      email: 'john@example.com',
    };

    const hashed = await hasher.hashIdsInData(data, new Set(['userId']));

    expect(hashed.userId).not.toBe('user_123');  // Hashed
    expect(hashed.name).toBe('John');              // Unchanged
    expect(hashed.email).toBe('john@example.com');  // Unchanged
  });
});

// =============================================================================
// Role-Based Scoping Tests
// =============================================================================

describe('RoleScopedRetrieval', () => {
  let retrieval: RoleScopedRetrieval;

  beforeEach(() => {
    retrieval = new RoleScopedRetrieval();
  });

  test('admin should get all data', () => {
    const data = {
      name: 'John',
      password: 'secret',
      email: 'john@example.com',
    };

    const result = retrieval.filterByRole(data, 'admin');

    expect(result).toEqual(data);
  });

  test('user should get restricted data', () => {
    const data = {
      name: 'John',
      password: 'secret',
      email: 'john@example.com',
    };

    const result = retrieval.filterByRole(data, 'user');

    expect(result.password).toBe('***REDACTED***');
    expect(result.email).toContain('***');
  });

  test('viewer should get public data only', () => {
    const data = {
      name: 'John',
      password: 'secret',
      email: 'john@example.com',
      description: 'Public profile',
    };

    const result = retrieval.filterByRole(data, 'viewer');

    expect(result.password).toBeUndefined();
    expect(result.email).toBeUndefined();
    expect(result.description).toBe('Public profile');
  });
});

// =============================================================================
// Context Assembly Integration Tests
// =============================================================================

describe('ContextAssemblyService', () => {
  let service: ContextAssemblyService;

  beforeEach(() => {
    service = new ContextAssemblyService({ enableAuditLogging: false });
  });

  describe('PII Redaction', () => {
    test('should redact PII in context', async () => {
      const result = await service.assembleContext({
        data: TEST_DATA_WITH_PII,
        userId: 'user_123',
        userRole: 'user',
        redactionLevel: RedactionLevel.MODERATE,
      });

      const context = result.assembledContext;

      // Email should be redacted
      expect(context.email).toContain('***@');

      // Phone should be redacted
      expect(context.phone).toContain('***-***-');

      // Should have PII detected in lineage
      expect(result.lineage.piiDetected.length).toBeGreaterThan(0);

      // Should have warnings
      expect(result.warnings.some(w => w.includes('PII detected'))).toBe(true);
    });
  });

  describe('Secret Redaction', () => {
    test('should redact secrets in context', async () => {
      const result = await service.assembleContext({
        data: TEST_DATA_WITH_SECRETS,
        userId: 'user_123',
        userRole: 'admin',
        redactionLevel: RedactionLevel.MODERATE,
      });

      const context = result.assembledContext;

      // Password should be redacted
      expect(context.password).toBe('***SECRET_REDACTED***');

      // API key should be redacted
      expect(context.apiKey).toContain('***SECRET_REDACTED***');

      // Should have secrets detected in lineage
      expect(result.lineage.secretsDetected.length).toBeGreaterThan(0);
    });
  });

  describe('Data Lineage', () => {
    test('should track data access lineage', async () => {
      const result = await service.assembleContext({
        data: { name: 'John', email: 'john@example.com' },
        userId: 'user_123',
        userRole: 'user',
      });

      const lineage = result.lineage;

      expect(lineage.userId).toBe('user_123');
      expect(lineage.userRole).toBe('user');
      expect(lineage.operation).toBe('assemble_context');
      expect(lineage.dataScope).toBeDefined();
      expect(lineage.redactionLevel).toBe(RedactionLevel.MODERATE);
      expect(lineage.fieldsAccessed.length).toBeGreaterThan(0);
      expect(lineage.inputHash).toBeDefined();
      expect(lineage.outputHash).toBeDefined();
      expect(lineage.processingTimeMs).toBeGreaterThan(0);
    });
  });

  describe('Redaction Levels', () => {
    test('should apply different redaction levels', async () => {
      const data = { email: 'john@example.com', phone: '555-123-4567' };

      const minimal = await service.assembleContext({
        data,
        userId: 'user_123',
        userRole: 'user',
        redactionLevel: RedactionLevel.MINIMAL,
      });

      const moderate = await service.assembleContext({
        data,
        userId: 'user_123',
        userRole: 'user',
        redactionLevel: RedactionLevel.MODERATE,
      });

      // Moderate should have more redaction than minimal
      expect(moderate.lineage.redactionLevel).toBe(RedactionLevel.MODERATE);
      expect(minimal.lineage.redactionLevel).toBe(RedactionLevel.MINIMAL);
    });
  });
});

// =============================================================================
// RAG Context Tests
// =============================================================================

describe('RAG Context Assembly', () => {
  let service: ContextAssemblyService;

  beforeEach(() => {
    service = new ContextAssemblyService({ enableAuditLogging: false });
  });

  test('should redact PII in RAG query', async () => {
    const result = await service.assembleRAGContext({
      query: RAG_QUERY_WITH_PII,
      documents: RAG_DOCUMENTS,
      userId: 'user_123',
      userRole: 'user',
      redactionLevel: RedactionLevel.MODERATE,
    });

    const query = result.assembledContext.query;

    // PII should be redacted
    expect(query).toContain('***');

    // Should detect PII
    expect(result.lineage.piiDetected.length).toBeGreaterThan(0);
  });

  test('should redact PII in RAG documents', async () => {
    const result = await service.assembleRAGContext({
      query: 'What is the contact info?',
      documents: RAG_DOCUMENTS,
      userId: 'user_123',
      userRole: 'user',
      redactionLevel: RedactionLevel.MODERATE,
    });

    const documents = result.assembledContext.documents;

    documents.forEach((doc: any) => {
      const content = doc.content;

      // Emails should be redacted
      if (content.toLowerCase().includes('email')) {
        expect(content).toContain('***@');
      }

      // SSNs should be redacted
      if (content.toLowerCase().includes('ssn')) {
        expect(content).toContain('***-**-****');
      }

      // Credit cards should be redacted
      if (content.toLowerCase().includes('credit card')) {
        expect(content).toContain('****-****-****-');
      }
    });
  });

  test('should include RAG-specific metadata', async () => {
    const result = await service.assembleRAGContext({
      query: 'Test query',
      documents: RAG_DOCUMENTS,
      userId: 'user_123',
      userRole: 'user',
    });

    expect(result.metadata.ragQuery).toBeDefined();
    expect(result.metadata.ragDocumentCount).toBe(RAG_DOCUMENTS.length);
  });
});

// =============================================================================
// Security Scenarios
// =============================================================================

describe('Security Scenarios', () => {
  let service: ContextAssemblyService;

  beforeEach(() => {
    service = new ContextAssemblyService({ enableAuditLogging: false });
  });

  test('should redact user PII in prompt', async () => {
    const prompt = {
      system: 'You are a helpful assistant.',
      userQuery: 'My email is john@example.com and my SSN is 123-45-6789',
    };

    const result = await service.assembleContext({
      data: prompt,
      userId: 'user_123',
      userRole: 'user',
      redactionLevel: RedactionLevel.MODERATE,
    });

    const userQuery = result.assembledContext.userQuery;

    expect(userQuery).toContain('***@');
    expect(userQuery).toContain('***-**-****');
    expect(result.assembledContext.system).toBe(prompt.system);
  });

  test('should handle cross-user data access', async () => {
    const otherUserData = {
      userId: 'user_789',
      name: 'Jane',
      email: 'jane@example.com',
    };

    const result = await service.assembleContext({
      data: otherUserData,
      userId: 'user_123',  // Different user
      userRole: 'user',
      redactionLevel: RedactionLevel.MODERATE,
    });

    // PII should be redacted
    expect(result.assembledContext.email).toContain('***');
  });

  test('should process batch RAG documents efficiently', async () => {
    const documents = [
      { id: '1', text: 'Email: bob@example.com' },
      { id: '2', text: 'SSN: 987-65-4321' },
      { id: '3', text: 'Card: 5555-1234-5678-9010' },
      { id: '4', text: 'Safe content' },
    ];

    const startTime = Date.now();
    const result = await service.assembleRAGContext({
      query: 'Summarize',
      documents,
      userId: 'user_123',
      userRole: 'user',
      redactionLevel: RedactionLevel.MODERATE,
    });
    const duration = Date.now() - startTime;

    // Should complete quickly
    expect(duration).toBeLessThan(100);

    // All PII should be redacted
    result.assembledContext.documents.forEach((doc: any) => {
      const text = doc.text;

      if (text.toLowerCase().includes('email')) {
        expect(text).toContain('***@');
      }
      if (text.toLowerCase().includes('ssn')) {
        expect(text).toContain('***-**-****');
      }
      if (text.toLowerCase().includes('card')) {
        expect(text).toContain('****-****-****-');
      }
    });
  });
});

// =============================================================================
// Convenience Functions
// =============================================================================

describe('Convenience Functions', () => {
  test('assembleSecureContext should work', async () => {
    const result = await assembleSecureContext(
      { email: 'john@example.com' },
      'user_123',
      'user',
      RedactionLevel.MODERATE
    );

    expect(result.assembledContext).toBeDefined();
    expect(result.lineage).toBeDefined();
  });

  test('redactPIIInText should work', () => {
    const text = 'Email: john@example.com, Phone: 555-123-4567';
    const redacted = redactPIIInText(text, RedactionLevel.MODERATE);

    expect(redacted).toContain('***@');
    expect(redacted).toContain('***-***-');
  });
});
