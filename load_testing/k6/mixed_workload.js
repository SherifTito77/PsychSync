/**
 * Mixed Workload Load Test for PsychSync using k6
 * Simulates realistic traffic patterns with multiple user types
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const requestRate = new Rate('request_success');
const responseTime = new Trend('response_time');

// Endpoints metrics
const authMetrics = {
  success: new Rate('auth_success'),
  latency: new Trend('auth_latency'),
};

const assessmentMetrics = {
  success: new Rate('assessment_success'),
  latency: new Trend('assessment_latency'),
};

const dashboardMetrics = {
  success: new Rate('dashboard_success'),
  latency: new Trend('dashboard_latency'),
};

const teamMetrics = {
  success: new Rate('team_success'),
  latency: new Trend('team_latency'),
};

export const options = {
  scenarios: {
    mixed_workload: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },   // Ramp up to 100 users
        { duration: '5m', target: 100 },   // Stay at 100 users
        { duration: '3m', target: 1000 },  // Ramp up to 1000 users
        { duration: '10m', target: 1000 }, // Stay at 1000 users
        { duration: '5m', target: 5000 },  // Ramp up to 5000 users
        { duration: '10m', target: 5000 }, // Stay at 5000 users
        { duration: '3m', target: 0 },     // Ramp down
      ],
      gracefulRampDown: '30s',
      tags: { scenario: 'mixed_workload' },
    },
  },
  thresholds: {
    'errors': ['rate<0.01'],
    'http_req_duration': ['p(95)<1000', 'p(99)<2000'],
    'auth_success': ['rate>0.95'],
    'assessment_success': ['rate>0.98'],
    'dashboard_success': ['rate>0.95'],
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Test data
const ASSESSMENT_IDS = ['mbti-001', 'big-five-001', 'enneagram-001', 'disc-001'];
const TEAM_IDS = ['team-001', 'team-002', 'team-003'];
const FRAMEWORKS = ['mbti', 'big_five', 'enneagram', 'predictive_index', 'disct'];

const TEST_USERS = Array.from({ length: 10000 }, (_, i) => ({
  email: `loadtest_user_${i}@test.com`,
  password: 'LoadTest123!',
}));

function getRandomUser() {
  return TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
}

function getRandomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// Authentication flow
function authenticateFlow() {
  const user = getRandomUser();
  const headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'PsychSync-LoadTest-k6/1.0',
  };

  group('Authentication', () => {
    // Login
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
      'login has token': (r) => r.json('access_token') !== undefined,
    });

    authMetrics.success.add(loginSuccess);
    authMetrics.latency.add(loginRes.timings.duration);
    errorRate.add(!loginSuccess);

    if (loginSuccess) {
      const token = loginRes.json('access_token');
      const authHeaders = { ...headers, 'Authorization': `Bearer ${token}` };

      // Token refresh (15% weight)
      if (Math.random() < 0.15) {
        const refreshRes = http.post(
          `${BASE_URL}${API_PREFIX}/auth/refresh`,
          JSON.stringify({ refresh_token: 'dummy' }),
          {
            headers: authHeaders,
            tags: { name: 'Auth:Refresh' },
          }
        );

        check(refreshRes, {
          'refresh successful': (r) => [200, 401].includes(r.status),
        });

        errorRate.add(refreshRes.status !== 200 && refreshRes.status !== 401);
      }

      return authHeaders;
    }
  });

  return null;
}

// Assessment flow (40% weight)
function assessmentFlow(authHeaders) {
  if (!authHeaders) return;

  group('Assessment Taking', () => {
    // Browse frameworks (10%)
    if (Math.random() < 0.10) {
      const browseRes = http.get(
        `${BASE_URL}${API_PREFIX}/personality-assessments/frameworks`,
        { headers: authHeaders, tags: { name: 'Assessment:Browse' } }
      );

      check(browseRes, { 'browse successful': (r) => r.status === 200 });
      assessmentMetrics.success.add(browseRes.status === 200);
      assessmentMetrics.latency.add(browseRes.timings.duration);
      errorRate.add(browseRes.status !== 200);
    }

    // Start assessment (8%)
    if (Math.random() < 0.08) {
      const framework = getRandomItem(FRAMEWORKS);
      const assessmentId = getRandomItem(ASSESSMENT_IDS);

      const startRes = http.post(
        `${BASE_URL}${API_PREFIX}/assessments/${assessmentId}/start`,
        JSON.stringify({ framework }),
        { headers: authHeaders, tags: { name: 'Assessment:Start' } }
      );

      check(startRes, { 'start successful': (r) => [200, 201].includes(r.status) });
      assessmentMetrics.success.add([200, 201].includes(startRes.status));
      assessmentMetrics.latency.add(startRes.timings.duration);
      errorRate.add(!check(startRes, { 'start ok': (r) => [200, 201].includes(r.status) }));
    }

    // Submit responses (15% - most frequent)
    if (Math.random() < 0.15) {
      const assessmentId = getRandomItem(ASSESSMENT_IDS);
      const responses = Array.from({ length: 5 }, (_, i) => ({
        question_id: `q${Math.floor(Math.random() * 100)}`,
        answer: Math.floor(Math.random() * 5) + 1,
      }));

      const submitRes = http.post(
        `${BASE_URL}${API_PREFIX}/assessments/${assessmentId}/responses`,
        JSON.stringify({ responses }),
        { headers: authHeaders, tags: { name: 'Assessment:Submit' } }
      );

      check(submitRes, { 'submit successful': (r) => [200, 201].includes(r.status) });
      assessmentMetrics.success.add([200, 201].includes(submitRes.status));
      assessmentMetrics.latency.add(submitRes.timings.duration);
      errorRate.add(!check(submitRes, { 'submit ok': (r) => [200, 201].includes(r.status) }));
    }

    // View results (7%)
    if (Math.random() < 0.07) {
      const assessmentId = getRandomItem(ASSESSMENT_IDS);

      const resultsRes = http.get(
        `${BASE_URL}${API_PREFIX}/assessments/${assessmentId}/results`,
        { headers: authHeaders, tags: { name: 'Assessment:Results' } }
      );

      check(resultsRes, { 'results successful': (r) => [200, 404].includes(r.status) });
      assessmentMetrics.success.add([200, 404].includes(resultsRes.status));
      assessmentMetrics.latency.add(resultsRes.timings.duration);
      errorRate.add(!check(resultsRes, { 'results ok': (r) => [200, 404].includes(r.status) }));
    }

    sleep(Math.random() * 2 + 1);
  });
}

// Dashboard flow (20% weight)
function dashboardFlow(authHeaders) {
  if (!authHeaders || Math.random() > 0.20) return;

  group('Dashboard & Analytics', () => {
    // Load dashboard (8%)
    if (Math.random() < 0.08) {
      const dashboardRes = http.get(
        `${BASE_URL}${API_PREFIX}/analytics/dashboard`,
        { headers: authHeaders, tags: { name: 'Dashboard:Load' } }
      );

      check(dashboardRes, { 'dashboard successful': (r) => r.status === 200 });
      dashboardMetrics.success.add(dashboardRes.status === 200);
      dashboardMetrics.latency.add(dashboardRes.timings.duration);
      errorRate.add(dashboardRes.status !== 200);
    }

    // Team analytics (6%)
    if (Math.random() < 0.06) {
      const teamId = getRandomItem(TEAM_IDS);

      const teamRes = http.get(
        `${BASE_URL}${API_PREFIX}/analytics/team/${teamId}`,
        { headers: authHeaders, tags: { name: 'Dashboard:Team' } }
      );

      check(teamRes, { 'team analytics successful': (r) => r.status === 200 });
      dashboardMetrics.success.add(teamRes.status === 200);
      dashboardMetrics.latency.add(teamRes.timings.duration);
      errorRate.add(teamRes.status !== 200);
    }

    // Trends (4%)
    if (Math.random() < 0.04) {
      const days = [7, 30, 90][Math.floor(Math.random() * 3)];

      const trendsRes = http.get(
        `${BASE_URL}${API_PREFIX}/analytics/trends?days=${days}`,
        { headers: authHeaders, tags: { name: 'Dashboard:Trends' } }
      );

      check(trendsRes, { 'trends successful': (r) => r.status === 200 });
      dashboardMetrics.success.add(trendsRes.status === 200);
      dashboardMetrics.latency.add(trendsRes.timings.duration);
      errorRate.add(trendsRes.status !== 200);
    }

    // Export report (2%)
    if (Math.random() < 0.02) {
      const format = ['pdf', 'csv', 'json'][Math.floor(Math.random() * 3)];

      const exportRes = http.get(
        `${BASE_URL}${API_PREFIX}/analytics/export?format=${format}`,
        { headers: authHeaders, tags: { name: 'Dashboard:Export' } }
      );

      check(exportRes, { 'export successful': (r) => [200, 202].includes(r.status) });
      dashboardMetrics.success.add([200, 202].includes(exportRes.status));
      dashboardMetrics.latency.add(exportRes.timings.duration);
      errorRate.add(!check(exportRes, { 'export ok': (r) => [200, 202].includes(r.status) }));
    }

    sleep(Math.random() * 2 + 1);
  });
}

// Team management flow (15% weight)
function teamFlow(authHeaders) {
  if (!authHeaders || Math.random() > 0.15) return;

  group('Team Management', () => {
    const teamId = getRandomItem(TEAM_IDS);

    // View team (6%)
    if (Math.random() < 0.06) {
      const viewRes = http.get(
        `${BASE_URL}${API_PREFIX}/teams/${teamId}`,
        { headers: authHeaders, tags: { name: 'Team:View' } }
      );

      check(viewRes, { 'view team successful': (r) => r.status === 200 });
      teamMetrics.success.add(viewRes.status === 200);
      teamMetrics.latency.add(viewRes.timings.duration);
      errorRate.add(viewRes.status !== 200);
    }

    // View members (4%)
    if (Math.random() < 0.04) {
      const membersRes = http.get(
        `${BASE_URL}${API_PREFIX}/teams/${teamId}/members`,
        { headers: authHeaders, tags: { name: 'Team:Members' } }
      );

      check(membersRes, { 'members successful': (r) => r.status === 200 });
      teamMetrics.success.add(membersRes.status === 200);
      teamMetrics.latency.add(membersRes.timings.duration);
      errorRate.add(membersRes.status !== 200);
    }

    // View activity (3%)
    if (Math.random() < 0.03) {
      const activityRes = http.get(
        `${BASE_URL}${API_PREFIX}/teams/${teamId}/activity`,
        { headers: authHeaders, tags: { name: 'Team:Activity' } }
      );

      check(activityRes, { 'activity successful': (r) => r.status === 200 });
      teamMetrics.success.add(activityRes.status === 200);
      teamMetrics.latency.add(activityRes.timings.duration);
      errorRate.add(activityRes.status !== 200);
    }

    // Update permissions (2%)
    if (Math.random() < 0.02) {
      const updateRes = http.put(
        `${BASE_URL}${API_PREFIX}/teams/${teamId}/permissions`,
        JSON.stringify({
          permissions: {
            view_analytics: Math.random() > 0.5,
            manage_assessments: Math.random() > 0.5,
          },
        }),
        { headers: authHeaders, tags: { name: 'Team:Update' } }
      );

      check(updateRes, { 'update successful': (r) => [200, 403].includes(r.status) });
      teamMetrics.success.add([200, 403].includes(updateRes.status));
      teamMetrics.latency.add(updateRes.timings.duration);
      errorRate.add(!check(updateRes, { 'update ok': (r) => [200, 403].includes(r.status) }));
    }

    sleep(Math.random() * 2 + 1);
  });
}

// AI/NLP flow (5% weight)
function aiFlow(authHeaders) {
  if (!authHeaders || Math.random() > 0.05) return;

  group('AI/NLP Processing', () => {
    // Text analysis (3%)
    if (Math.random() < 0.03) {
      const texts = [
        'I feel confident in my ability to lead teams effectively.',
        'Communication is key to successful project outcomes.',
        'I prefer working independently rather than in groups.',
      ];

      const analyzeRes = http.post(
        `${BASE_URL}${API_PREFIX}/nlp/analyze`,
        JSON.stringify({
          text: texts[Math.floor(Math.random() * texts.length)],
          analysis_type: ['sentiment', 'personality'][Math.floor(Math.random() * 2)],
        }),
        { headers: authHeaders, tags: { name: 'AI:Analyze' } }
      );

      check(analyzeRes, { 'analysis successful': (r) => [200, 202].includes(r.status) });
      errorRate.add(!check(analyzeRes, { 'analysis ok': (r) => [200, 202].includes(r.status) }));
    }

    // Get insights (2%)
    if (Math.random() < 0.02) {
      const assessmentId = getRandomItem(ASSESSMENT_IDS);

      const insightsRes = http.get(
        `${BASE_URL}${API_PREFIX}/ai/insights/${assessmentId}`,
        { headers: authHeaders, tags: { name: 'AI:Insights' } }
      );

      check(insightsRes, { 'insights successful': (r) => [200, 404].includes(r.status) });
      errorRate.add(!check(insightsRes, { 'insights ok': (r) => [200, 404].includes(r.status) }));
    }

    sleep(Math.random() * 3 + 2);
  });
}

// Main test
export default function() {
  const authHeaders = authenticateFlow();

  // Execute different flows based on weights
  // 40% Assessment, 20% Dashboard, 15% Team, 5% AI
  const rand = Math.random();

  if (rand < 0.40) {
    assessmentFlow(authHeaders);
  } else if (rand < 0.60) {
    dashboardFlow(authHeaders);
  } else if (rand < 0.75) {
    teamFlow(authHeaders);
  } else {
    aiFlow(authHeaders);
  }

  // Base think time
  sleep(Math.random() * 2 + 1);
}

export function setup() {
  console.log(`Starting mixed workload test against: ${BASE_URL}`);
  console.log('Task Distribution:');
  console.log('  - Authentication: 15%');
  console.log('  - Assessment Taking: 40%');
  console.log('  - Dashboard & Analytics: 20%');
  console.log('  - Team Management: 15%');
  console.log('  - AI/NLP Processing: 10%');

  return { startTime: new Date().toISOString() };
}

export function teardown(data) {
  console.log('\n=== TEST SUMMARY ===');
  console.log(`Start: ${data.startTime}`);
  console.log(`End: ${new Date().toISOString()}`);
  console.log('====================\n');
}
