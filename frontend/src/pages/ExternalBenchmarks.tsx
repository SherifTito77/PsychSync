import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface BenchmarkComparison {
  metric: string;
  org_score: number;
  peer_avg: number;
  percentile: number;
  direction: 'higher_better' | 'lower_better';
}

function ExternalBenchmarks() {
  const [optedIn, setOptedIn] = useState(false);
  const [comparisons, setComparisons] = useState<BenchmarkComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState(false);

  const orgId = 'current';

  const fetchOptInStatus = useCallback(async () => {
    try {
      const res = await axios.get(`/api/v1/external-benchmarks/opt-in/${orgId}`);
      setOptedIn(res.data.opted_in || false);
    } catch {
      setOptedIn(false);
    }
  }, [orgId]);

  const fetchComparisons = useCallback(async () => {
    try {
      const res = await axios.get(`/api/v1/external-benchmarks/compare/${orgId}`);
      setComparisons(res.data.comparisons || res.data || []);
    } catch {
      setComparisons([]);
    }
  }, [orgId]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([fetchOptInStatus(), fetchComparisons()])
      .catch(() => { if (!cancelled) setError('Failed to load benchmark data'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [fetchOptInStatus, fetchComparisons]);

  const handleToggleOptIn = async () => {
    setToggling(true);
    setError(null);
    try {
      await axios.post(`/api/v1/external-benchmarks/opt-in/${orgId}`);
      await fetchOptInStatus();
      if (!optedIn) {
        await fetchComparisons();
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update opt-in status');
    } finally {
      setToggling(false);
    }
  };

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

      {error && (
        <div style={{
          padding: 16, background: '#fef2f2', border: '1px solid #fecaca',
          borderRadius: 8, color: '#991b1b', marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#9ca3af' }}>Loading benchmark data...</div>
      ) : !optedIn ? (
        <div style={{ textAlign: 'center', padding: 48, background: '#f9fafb', borderRadius: 16 }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>📊</div>
          <h3 style={{ fontSize: 20, fontWeight: 600, color: '#374151', marginBottom: 8 }}>Opt In to Benchmarking</h3>
          <p style={{ fontSize: 14, color: '#6b7280', maxWidth: 500, margin: '0 auto 24px' }}>
            Share anonymized org-level scores to see how you compare against industry peers. You can opt out at any time.
          </p>
          <button
            onClick={handleToggleOptIn}
            disabled={toggling}
            style={{ padding: '12px 28px', background: toggling ? '#9ca3af' : '#4f46e5', color: '#fff', border: 'none', borderRadius: 8, cursor: toggling ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: 15 }}
          >
            {toggling ? 'Processing...' : 'Opt In'}
          </button>
        </div>
      ) : (
        <div>
          {/* Metrics grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
            {metrics.map(m => {
              const comp = comparisons.find(c => c.metric === m.key);
              return (
                <div key={m.key} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <span style={{ fontSize: 24 }}>{m.icon}</span>
                    <span style={{ fontWeight: 600 }}>{m.label}</span>
                  </div>
                  {comp ? (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 24, fontWeight: 700, color: '#4f46e5' }}>{comp.org_score.toFixed(1)}</div>
                          <div style={{ fontSize: 11, color: '#9ca3af' }}>Your Org</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 24, fontWeight: 700, color: '#6b7280' }}>{comp.peer_avg.toFixed(1)}</div>
                          <div style={{ fontSize: 11, color: '#9ca3af' }}>Peer Avg</div>
                        </div>
                      </div>
                      <div style={{ background: '#f3f4f6', borderRadius: 4, height: 8, position: 'relative' }}>
                        <div style={{
                          width: `${Math.min(comp.percentile, 100)}%`, height: '100%',
                          background: comp.percentile >= 75 ? '#22c55e' : comp.percentile >= 50 ? '#eab308' : '#ef4444',
                          borderRadius: 4,
                        }} />
                      </div>
                      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4, textAlign: 'right' }}>
                        {comp.percentile}th percentile
                      </div>
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: 13, padding: 16 }}>
                      Awaiting peer data (minimum 5 orgs)
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <button
              onClick={handleToggleOptIn}
              disabled={toggling}
              style={{ padding: '8px 16px', background: 'transparent', color: '#ef4444', border: '1px solid #ef4444', borderRadius: 8, cursor: toggling ? 'not-allowed' : 'pointer', fontSize: 13 }}
            >
              {toggling ? 'Processing...' : 'Opt Out'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExternalBenchmarks;
