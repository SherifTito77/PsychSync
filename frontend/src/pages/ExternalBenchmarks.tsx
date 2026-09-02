import { useState } from 'react';

interface BenchmarkComparison {
  metric: string;
  org_score: number;
  peer_avg: number;
  percentile: number;
  direction: 'higher_better' | 'lower_better';
}

function ExternalBenchmarks() {
  const [optedIn, setOptedIn] = useState(false);
  const [comparisons] = useState<BenchmarkComparison[]>([]);

  const metrics = [
    { key: 'team_health', label: 'Team Health', icon: '💪' },
    { key: 'collaboration', label: 'Collaboration', icon: '🤝' },
    { key: 'psychological_safety', label: 'Psych Safety', icon: '🛡️' },
    { key: 'manager_health', label: 'Manager Health', icon: '👔' },
    { key: 'change_readiness', label: 'Change Readiness', icon: '🔄' },
    { key: 'burnout_risk', label: 'Burnout Risk', icon: '🔥' },
    { key: 'friction_index', label: 'Friction Index', icon: '⚡' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>External Benchmarks</h1>
      <p style={{ color: '#6b7280', marginBottom: 24 }}>
        Compare your organization against anonymized peers with differential privacy protection.
      </p>

      {/* Privacy info */}
      <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12, padding: 16, marginBottom: 24, display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <span style={{ fontSize: 24 }}>🔐</span>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14 }}>Differential Privacy</div>
          <div style={{ fontSize: 13, color: '#4b5563' }}>
            All benchmark aggregates include Laplace noise (epsilon=1.0). Minimum 5 peer organizations required. Your data is never individually identifiable.
          </div>
        </div>
      </div>

      {!optedIn ? (
        <div style={{ textAlign: 'center', padding: 48, background: '#f9fafb', borderRadius: 16 }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>📊</div>
          <h3 style={{ fontSize: 20, fontWeight: 600, color: '#374151', marginBottom: 8 }}>Opt In to Benchmarking</h3>
          <p style={{ fontSize: 14, color: '#6b7280', maxWidth: 500, margin: '0 auto 24px' }}>
            Share anonymized org-level scores to see how you compare against industry peers. You can opt out at any time.
          </p>
          <button
            onClick={() => setOptedIn(true)}
            style={{ padding: '12px 28px', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: 15 }}
          >
            Opt In
          </button>
        </div>
      ) : (
        <div>
          {/* Metrics grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
            {metrics.map(m => (
              <div key={m.key} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <span style={{ fontSize: 24 }}>{m.icon}</span>
                  <span style={{ fontWeight: 600 }}>{m.label}</span>
                </div>
                <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: 13, padding: 16 }}>
                  Contribute data to see benchmark comparison
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <button
              onClick={() => setOptedIn(false)}
              style={{ padding: '8px 16px', background: 'transparent', color: '#ef4444', border: '1px solid #ef4444', borderRadius: 8, cursor: 'pointer', fontSize: 13 }}
            >
              Opt Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExternalBenchmarks;
