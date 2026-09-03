/**
 * Authentication Load Test for PsychSync using k6
 * Tests login, token refresh, and logout under concurrent load
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const loginSuccessRate = new Rate('login_success');
const authLatency = new Trend('auth_latency');

// Test configuration
export const options = {
  scenarios: {
    small_load: {
      executor: 'constant-vus',
      vus: 100,
      duration: '5m',
      gracefulStop: '30s',
      tags: { scenario: 'small' },
    },
    medium_load: {
      executor: 'constant-vus',
      vus: 1000,
      duration: '10m',
      startTime: '5m',
      gracefulStop: '30s',
      tags: { scenario: 'medium' },
    },
    large_load: {
      executor: 'constant-vus',
      vus: 10000,
      duration: '20m',
      startTime: '15m',
      gracefulStop: '30s',
      tags: { scenario: 'large' },
    },
  },
  thresholds: {
    'errors': ['rate<0.01'], // Error rate must be below 1%
    'http_req_duration': ['p(95)<500', 'p(99)<1000'], // Response time thresholds
    'login_success': ['rate>0.99'], // 99%+ login success rate
  },
};

// Configuration
const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Test user pool
const TEST_USERS = Array.from({ length: 10000 }, (_, i) => ({
  email: `loadtest_user_${i}@test.com`,
  password: 'LoadTest123!',
}));

// Get random test user
function getRandomUser() {
  return TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
}

// Setup function - runs once before test
export function setup() {
  console.log(`Starting authentication load test against: ${BASE_URL}`);
  console.log(`Total users in pool: ${TEST_USERS.length}`);

  // Optionally pre-create test users here
  // or verify API is accessible
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    console.error('API health check failed!');
  }

  return { startTime: new Date().toISOString() };
}

// Main test function - runs for each VU
export default function(data) {
  const user = getRandomUser();
  const headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'PsychSync-LoadTest-k6/1.0',
  };

  // Task 1: Login (weight: 7)
  if (Math.random() < 0.7) {
    const loginRes = http.post(
      `${BASE_URL}${API_PREFIX}/auth/token-fixed`,
      `username=${encodeURIComponent(user.email)}&password=${encodeURIComponent(user.password)}`,
      {
        headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded' },
        tags: { name: 'Auth:Login' },
      }
    );

    const loginSuccess = check(loginRes, {
      'login status is 200': (r) => r.status === 200,
      'login has access token': (r) => r.json('access_token') !== undefined,
      'login response time < 500ms': (r) => r.timings.duration < 500,
    });

    loginSuccessRate.add(loginSuccess);
    errorRate.add(!loginSuccess);
    authLatency.add(loginRes.timings.duration);

    if (loginSuccess) {
      const token = loginRes.json('access_token');

      // Store token for subsequent requests
      const authHeaders = {
        ...headers,
        'Authorization': `Bearer ${token}`,
      };

      // Task 2: Token refresh (weight: 2)
      if (Math.random() < 0.2) {
        const refreshRes = http.post(
          `${BASE_URL}${API_PREFIX}/auth/refresh`,
          JSON.stringify({ refresh_token: 'dummy_refresh_token' }),
          {
            headers: authHeaders,
            tags: { name: 'Auth:Refresh' },
          }
        );

        check(refreshRes, {
          'refresh status is 200 or 401': (r) => [200, 401].includes(r.status),
          'refresh response time < 300ms': (r) => r.timings.duration < 300,
        });

        errorRate.add(refreshRes.status !== 200 && refreshRes.status !== 401);
      }

      // Task 3: Verify current user (weight: 1)
      if (Math.random() < 0.1) {
        const verifyRes = http.get(
          `${BASE_URL}${API_PREFIX}/users/me`,
          {
            headers: authHeaders,
            tags: { name: 'Auth:Verify' },
          }
        );

        check(verifyRes, {
          'verify status is 200': (r) => r.status === 200,
          'verify response time < 200ms': (r) => r.timings.duration < 200,
        });

        errorRate.add(verifyRes.status !== 200);
      }

      // Task 4: Logout (weight: 0.5)
      if (Math.random() < 0.05) {
        const logoutRes = http.post(
          `${BASE_URL}${API_PREFIX}/auth/logout`,
          null,
          {
            headers: authHeaders,
            tags: { name: 'Auth:Logout' },
          }
        );

        check(logoutRes, {
          'logout status is 200 or 204': (r) => [200, 204].includes(r.status),
          'logout response time < 300ms': (r) => r.timings.duration < 300,
        });

        errorRate.add(logoutRes.status !== 200 && logoutRes.status !== 204);
      }
    }

    // Think time between requests (1-3 seconds)
    sleep(Math.random() * 2 + 1);
  }

  // Simulate concurrent device login (weight: 0.5)
  if (Math.random() < 0.05) {
    const deviceId = `device_${Math.floor(Math.random() * 1000)}`;

    const concurrentLoginRes = http.post(
      `${BASE_URL}${API_PREFIX}/auth/token-fixed`,
      `username=${encodeURIComponent(user.email)}&password=${encodeURIComponent(user.password)}&device_id=${deviceId}`,
      {
        headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded' },
        tags: { name: 'Auth:ConcurrentLogin' },
      }
    );

    check(concurrentLoginRes, {
      'concurrent login status is 200': (r) => r.status === 200,
      'concurrent login response time < 500ms': (r) => r.timings.duration < 500,
    });

    errorRate.add(concurrentLoginRes.status !== 200);
    sleep(Math.random() * 2 + 1);
  }
}

// Teardown function - runs once after test
export function teardown(data) {
  console.log('Test completed');
  console.log(`Start time: ${data.startTime}`);
  console.log(`End time: ${new Date().toISOString()}`);
}
