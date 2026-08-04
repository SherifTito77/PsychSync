/**
 * PsychSync Load Testing Script
 *
 * Tests clinical platform performance under load:
 * - Screening submission endpoint
 * - Analytics endpoints
 * - Authentication flow
 * - Crisis alert creation
 *
 * USAGE:
 *   k6 run load_test_clinical.js
 *   k6 run --vus 1000 --duration 30m load_test_clinical.js
 *   k6 run -e BASE_URL=http://localhost:8000 load_test_clinical.js
 *
 * REQUIREMENTS:
 *   - k6 installed (https://k6.io)
 *   - PsychSync API running
 *   - Test database configured
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Configuration
export const DURATION = '10m'; // Test duration
export const VUS = 100; // Virtual users
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Custom metrics
const errorRate = new Rate('errors');
const screeningSuccessRate = new Rate('screening_success');

// Test data
const testUser = {
  email: `test${Math.random()}@example.com`,
  password: 'TestPassword123!',
  full_name: 'Test User'
};

const screeningData = {
  phq9: {
    q1_interest: 1,
    q2_depressed: 1,
    q3_sleep: 1,
    q4_energy: 1,
    q5_appetite: 1,
    q6_self_worth: 1,
    q7_concentration: 1,
    q8_motor: 1,
    q9_suicide: 0  // No suicide risk for load testing
  },
  gad7: {
    q1_nervous: 1,
    q2_control_worry: 1,
    q3_worry_too_much: 1,
    q4_trouble_relaxing: 1,
    q5_restless: 1,
    q6_irritable: 1,
    q7_afraid: 1
  }
};

// ============================================================================
// AUTHENTICATION FLOW
// ============================================================================

export function setup() {
  // Setup: Create test user and get auth token
  const registerUrl = `${BASE_URL}/api/v1/simple_auth/register`;
  const loginUrl = `${BASE_URL}/api/v1/simple_auth/login`;

  // Register test user
  const registerPayload = JSON.stringify(testUser);

  const registerRes = http.post(registerUrl, registerPayload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'Register' }
  });

  check(registerRes, 'Registration successful', {
    registerRes.status === 200 || registerRes.status === 201 || registerRes.status === 400
  });

  // Login to get token
  const loginPayload = JSON.stringify({
    email: testUser.email,
    password: testUser.password
  });

  const loginRes = http.post(loginUrl, loginPayload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'Login' }
  });

  check(loginRes, 'Login successful', { loginRes.status === 200 });

  const token = loginRes.json('access_token');
  return { token };
}

// ============================================================================
// MAIN TEST SCENARIOS
// ============================================================================

export default function(data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`
  };

  // Scenario 1: Health Check (baseline)
  healthCheck(headers);

  // Scenario 2: Submit PHQ-9 Screening
  submitPHQ9(headers);

  // Scenario 3: Submit GAD-7 Screening
  submitGAD7(headers);

  // Scenario 4: Get Analytics
  getAnalytics(headers);

  // Scenario 5: Get Notifications
  getNotifications(headers);

  // Small delay between iterations
  sleep(1);
}

// ============================================================================
// TEST FUNCTIONS
// ============================================================================

function healthCheck(headers) {
  const res = http.get(`${BASE_URL}/api/v1/health`, {
    headers,
    tags: { name: 'HealthCheck' }
  });

  const success = check(res, {
    'Health check successful': (r) => r.status === 200,
    'Response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!success);
}

function submitPHQ9(headers) {
  const res = http.post(
    `${BASE_URL}/api/v1/screening/phq9`,
    JSON.stringify(screeningData.phq9),
    {
      headers,
      tags: { name: 'SubmitPHQ9' }
    }
  );

  const success = check(res, {
    'PHQ-9 submission successful': (r) => r.status === 200,
    'Response time < 2s': (r) => r.timings.duration < 2000,
    'Has screening result': (r) => r.json('total_score') !== undefined,
  });

  screeningSuccessRate.add(success);
  errorRate.add(!success);

  if (success) {
    const result = res.json();
    check(result, {
      'Has severity level': (r) => r.severity_level !== undefined,
      'Has risk level': (r) => r.risk_level !== undefined,
      'No false crisis alert': (r) => r.crisis_alert === false,
    });
  }
}

function submitGAD7(headers) {
  const res = http.post(
    `${BASE_URL}/api/v1/screening/gad7`,
    JSON.stringify(screeningData.gad7),
    {
      headers,
      tags: { name: 'SubmitGAD7' }
    }
  );

  const success = check(res, {
    'GAD-7 submission successful': (r) => r.status === 200,
    'Response time < 2s': (r) => r.timings.duration < 2000,
  });

  errorRate.add(!success);
}

function getAnalytics(headers) {
  const res = http.get(
    `${BASE_URL}/api/v1/analytics/clinical/completion-stats?start_date=2025-01-01&end_date=2025-01-15`,
    {
      headers,
      tags: { name: 'GetAnalytics' }
    }
  );

  check(res, {
    'Analytics request successful': (r) => r.status === 200,
    'Response time < 5s': (r) => r.timings.duration < 5000,
    'Has analytics data': (r) => r.json('total_eligible') !== undefined,
  });
}

function getNotifications(headers) {
  const res = http.get(
    `${BASE_URL}/api/v1/notifications`,
    {
      headers,
      tags: { name: 'GetNotifications' }
    }
  );

  check(res, {
    'Notifications request successful': (r) => r.status === 200,
    'Response time < 1s': (r) => r.timings.duration < 1000,
  });
}

// ============================================================================
// LOAD TESTING STAGES
// ============================================================================

export let options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '3m', target: 50 },   // Ramp up to 50 users
    { duration: '3m', target: 100 },  // Ramp up to 100 users
    { duration: '2m', target: 200 },  // Spike to 200 users
    { duration: '2m', target: 50 },   // Scale down to 50 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    http_req_failed: ['rate<0.01'],     // Error rate < 1%
    screening_success_rate: ['rate>0.95'], // 95% success rate
  },
  discardResponseBodies: true,
  maxRedirects: 10
};

// Output HTML report (optional)
export { handleSummary } from './summary_module.js';

// ============================================================================
// STRESS TEST (Optional - Use with caution)
// ============================================================================

export function stressTest() {
  // More aggressive load test
  export let options = {
    stages: [
      { duration: '1m', target: 100 },
      { duration: '2m', target: 500 },
      { duration: '2m', target: 1000 }, // Stress level
      { duration: '1m', target: 0 },
    ],
    thresholds: {
      http_req_duration: ['p(95)<5000'], // Allow 5s during stress
      http_req_failed: ['rate<0.05'],     // Allow 5% errors during stress
    },
  };
}

// ============================================================================
// SOAK TEST (Long duration, low load)
// ============================================================================

export function soakTest() {
  // Long duration test to find memory leaks
  export let options = {
    stages: [
      { duration: '1h', target: 20 }, // 20 users for 1 hour
    ],
    thresholds: {
      http_req_duration: ['p(95)<1000'], // Should stay fast
      http_req_failed: ['rate<0.01'],     // No degradation
    },
  };
}

// ============================================================================
// SPIKE TEST (Sudden traffic spike)
// ============================================================================

export function spikeTest() {
  // Simulate sudden traffic spike (e.g., after email notification)
  export let options = {
    stages: [
      { duration: '1m', target: 10 },
    { duration: '30s', target: 500 },  // Spike!
    { duration: '2m', target: 10 },
  ],
    thresholds: {
    http_req_duration: ['p(95)<3000'], // Allow slower during spike
    http_req_failed: ['rate<0.05'],     // Allow 5% errors
    },
  };
}
