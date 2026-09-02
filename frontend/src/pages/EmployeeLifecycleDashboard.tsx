import { useState, useEffect } from 'react';
import axios from '../api/axios';

interface TurnoverData {
  total_rate: number;
  voluntary_rate: number;
  involuntary_rate: number;
  regrettable_rate: number;
}

interface DepartureCluster {
  group: string;
  departures: number;
  z_score: number;
  severity: string;
  org_avg_departures: number;
}

interface LifecycleAnalysis {
  org_id: string;
  analysis_period_days: number;
  turnover: TurnoverData;
  promotion_rate: number;
  internal_mobility_rate: number;
  avg_tenure_months: number;
  tenure_distribution: Record<string, number>;
  manager_change_frequency: number;
  new_hire_90day_retention: number;
  tenure_cliff_month: number | null;
  departure_clustering: DepartureCluster[];
  promotion_equity: Record<string, number>;
  flight_risk_indicators: Record<string, number>;
}

const SEVERITY_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  critical: { bg: '#fef2f2', border: '#fecaca', text: '#991b1b' },
  high: { bg: '#fff7ed', border: '#fed7aa', text: '#9a3412' },
  elevated: { bg: '#fffbeb', border: '#fde68a', text: '#92400e' },
};

function StatCard({ label, value, subtext }: { label: string; value: string | number; subtext?: string }) {
  return (
    <div style={{
      background: '#fff', padding: 20, borderRadius: 12,
      border: '1px solid #e5e7eb', flex: 1, minWidth: 160,
    }}>
      <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 500, marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: '#111827' }}>{value}</div>
      {subtext && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>{subtext}</div>}
    </div>
  );
}

function TurnoverBar({ label, rate, color }: { label: string; rate: number; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
      <div style={{ width: 140, fontSize: 13, color: '#374151', flexShrink: 0 }}>{label}</div>
      <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 4, height: 22, position: 'relative' }}>
        <div
          style={{
            width: `${Math.min(rate, 50)}%`, height: '100%',
            background: color, borderRadius: 4,
            transition: 'width 0.6s ease',
          }}
        />
        <span style={{
          position: 'absolute', right: 8, top: 2,
          fontSize: 12, fontWeight: 600, color: '#374151',
        }}>
          {rate.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

function TenureDistribution({ data }: { data: Record<string, number> }) {
  const buckets = ['0-6m', '6-12m', '1-2y', '2-5y', '5y+'];
  const maxVal = Math.max(...Object.values(data), 1);
  const colors = ['#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'];

  return (
    <div style={{
      background: '#fff', padding: 20, borderRadius: 12,
      border: '1px solid #e5e7eb',
    }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16, color: '#374151' }}>
        Tenure Distribution
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 120 }}>
        {buckets.map((bucket, i) => {
          const count = data[bucket] || 0;
          const height = (count / maxVal) * 100;
          return (
            <div key={bucket} style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 4 }}>
                {count}
              </div>
              <div style={{
                height: `${Math.max(height, 4)}%`, background: colors[i],
                borderRadius: '4px 4px 0 0', transition: 'height 0.4s ease',
                minHeight: 4,
              }} />
              <div style={{ fontSize: 10, color: '#6b7280', marginTop: 6 }}>{bucket}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PromotionEquityChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort(([, a], [, b]) => b - a);
  if (entries.length === 0) {
    return <div style={{ color: '#9ca3af', fontSize: 13, textAlign: 'center', padding: 40 }}>No promotion data available</div>;
  }

  const rates = entries.map(([, r]) => r);
  const orgAvg = rates.reduce((a, b) => a + b, 0) / rates.length;
  const maxRate = Math.max(...rates, 1);

  return (
    <div style={{
      background: '#fff', padding: 20, borderRadius: 12,
      border: '1px solid #e5e7eb',
    }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4, color: '#374151' }}>
        Promotion Equity by Department
      </div>
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 16 }}>
        Org average: {orgAvg.toFixed(1)}% | Flagged if &lt; {(orgAvg * 0.5).toFixed(1)}% or &gt; {(orgAvg * 2).toFixed(1)}%
      </div>
      {entries.map(([dept, rate]) => {
        const flagged = orgAvg > 0 && (rate < orgAvg * 0.5 || rate > orgAvg * 2);
        return (
          <div key={dept} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <div style={{
              width: 140, fontSize: 13, flexShrink: 0,
              color: flagged ? '#dc2626' : '#374151',
              fontWeight: flagged ? 600 : 400,
            }}>
              {dept} {flagged ? '(!)' : ''}
            </div>
            <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 4, height: 20, position: 'relative' }}>
              <div style={{
                width: `${(rate / maxRate) * 100}%`, height: '100%',
                background: flagged ? '#fbbf24' : '#10b981',
                borderRadius: 4, transition: 'width 0.6s ease',
              }} />
              <span style={{
                position: 'absolute', right: 8, top: 1,
                fontSize: 12, fontWeight: 600, color: '#374151',
              }}>
                {rate.toFixed(1)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function FlightRiskIndicators({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort(([, a], [, b]) => b - a);
  if (entries.length === 0) {
    return <div style={{ color: '#9ca3af', fontSize: 13, textAlign: 'center', padding: 40 }}>No flight risk data</div>;
  }

  return (
    <div style={{
      background: '#fff', padding: 20, borderRadius: 12,
      border: '1px solid #e5e7eb',
    }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16, color: '#374151' }}>
        Flight Risk by Team / Department
      </div>
      {entries.map(([group, risk]) => {
        const color = risk >= 60 ? '#ef4444' : risk >= 35 ? '#f59e0b' : '#10b981';
        return (
          <div key={group} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <div style={{ width: 160, fontSize: 13, color: '#374151', flexShrink: 0 }}>
              {group.length > 20 ? group.slice(0, 8) + '...' : group}
            </div>
            <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 4, height: 22, position: 'relative' }}>
              <div style={{
                width: `${Math.min(risk, 100)}%`, height: '100%',
                background: color, borderRadius: 4,
                transition: 'width 0.6s ease',
              }} />
              <span style={{
                position: 'absolute', right: 8, top: 2,
                fontSize: 12, fontWeight: 600,
                color: risk > 60 ? '#fff' : '#374151',
              }}>
                {risk.toFixed(0)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function EmployeeLifecycleDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'risk' | 'equity'>('overview');
  const [analysis, setAnalysis] = useState<LifecycleAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = 'current';

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`/api/v1/employee-lifecycle/${orgId}/analysis`);
        if (!cancelled) {
          setAnalysis(res.data);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.response?.data?.detail || 'Failed to load lifecycle analytics');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();
    return () => { cancelled = true; };
  }, [orgId]);

  const tabs = [
    { key: 'overview' as const, label: 'Overview' },
    { key: 'risk' as const, label: 'Risk Signals' },
    { key: 'equity' as const, label: 'Equity & Mobility' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>
          Employee Lifecycle Analytics
        </h1>
        <p style={{ color: '#6b7280', fontSize: 14 }}>
          Organizational patterns from HRIS lifecycle events. Structural signals, not individual sentiment.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 20px', border: 'none', cursor: 'pointer',
              fontSize: 14, fontWeight: activeTab === tab.key ? 600 : 400,
              color: activeTab === tab.key ? '#4f46e5' : '#6b7280',
              borderBottom: activeTab === tab.key ? '2px solid #4f46e5' : '2px solid transparent',
              background: 'transparent',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>
          Loading lifecycle analytics...
        </div>
      )}

      {error && (
        <div style={{
          padding: 16, background: '#fef2f2', border: '1px solid #fecaca',
          borderRadius: 8, color: '#991b1b', marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {/* ===== OVERVIEW TAB ===== */}
      {!loading && !error && analysis && activeTab === 'overview' && (
        <>
          {/* Top stats */}
          <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
            <StatCard label="Total Turnover Rate" value={`${analysis.turnover.total_rate}%`} subtext="Annualized" />
            <StatCard label="Promotion Rate" value={`${analysis.promotion_rate}%`} subtext="Period" />
            <StatCard label="Avg Tenure" value={`${analysis.avg_tenure_months.toFixed(0)}mo`} />
            <StatCard label="90-Day Retention" value={`${analysis.new_hire_90day_retention}%`} subtext="New hires" />
          </div>

          {/* Turnover breakdown */}
          <div style={{
            background: '#fff', padding: 20, borderRadius: 12,
            border: '1px solid #e5e7eb', marginBottom: 24,
          }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16, color: '#374151' }}>
              Turnover Breakdown (Annualized)
            </div>
            <TurnoverBar label="Voluntary" rate={analysis.turnover.voluntary_rate} color="#f97316" />
            <TurnoverBar label="Involuntary" rate={analysis.turnover.involuntary_rate} color="#8b5cf6" />
            <TurnoverBar label="Regrettable" rate={analysis.turnover.regrettable_rate} color="#ef4444" />
          </div>

          {/* Tenure distribution */}
          <TenureDistribution data={analysis.tenure_distribution} />
        </>
      )}

      {/* ===== RISK SIGNALS TAB ===== */}
      {!loading && !error && analysis && activeTab === 'risk' && (
        <>
          {/* Tenure cliff */}
          {analysis.tenure_cliff_month !== null && (
            <div style={{
              padding: 20, background: '#fffbeb', border: '1px solid #fde68a',
              borderRadius: 12, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <div style={{ fontSize: 40, lineHeight: 1 }}>
                {analysis.tenure_cliff_month <= 12 ? '/!\\' : '/!\\'}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 16, color: '#92400e', marginBottom: 4 }}>
                  Tenure Cliff Detected: Month {analysis.tenure_cliff_month}
                </div>
                <div style={{ fontSize: 13, color: '#78350f' }}>
                  Most departures cluster around month {analysis.tenure_cliff_month} of employment.
                  {analysis.tenure_cliff_month <= 6 && ' Early attrition may indicate onboarding issues.'}
                  {analysis.tenure_cliff_month > 6 && analysis.tenure_cliff_month <= 14 && ' This is a common 1-year cliff — employees leave after their first anniversary.'}
                  {analysis.tenure_cliff_month > 14 && analysis.tenure_cliff_month <= 26 && ' Two-year cliff — employees may be hitting growth ceilings.'}
                  {analysis.tenure_cliff_month > 26 && ' Late-stage departures often indicate career stagnation or market pull.'}
                </div>
              </div>
            </div>
          )}

          {/* Departure clustering */}
          <div style={{
            background: '#fff', padding: 20, borderRadius: 12,
            border: '1px solid #e5e7eb', marginBottom: 24,
          }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16, color: '#374151' }}>
              Departure Clusters
            </div>
            {analysis.departure_clustering.length === 0 ? (
              <div style={{ color: '#10b981', fontSize: 13, padding: '20px 0', textAlign: 'center' }}>
                No abnormal departure clustering detected. Turnover is evenly distributed.
              </div>
            ) : (
              analysis.departure_clustering.map((cluster, i) => {
                const sev = SEVERITY_COLORS[cluster.severity] || SEVERITY_COLORS.elevated;
                return (
                  <div key={i} style={{
                    padding: '14px 18px', marginBottom: 10, borderRadius: 8,
                    background: sev.bg, border: `1px solid ${sev.border}`,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, color: sev.text }}>
                        {cluster.group.length > 20 ? cluster.group.slice(0, 8) + '...' : cluster.group}
                      </div>
                      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                        {cluster.departures} departures (org avg: {cluster.org_avg_departures})
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 20, fontWeight: 700, color: sev.text }}>
                        {cluster.z_score.toFixed(1)}z
                      </div>
                      <div style={{
                        fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                        color: sev.text, letterSpacing: 0.5,
                      }}>
                        {cluster.severity}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Flight risk indicators */}
          <FlightRiskIndicators data={analysis.flight_risk_indicators} />

          {/* Manager change frequency */}
          <div style={{
            marginTop: 24, padding: 20, background: '#fff', borderRadius: 12,
            border: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', gap: 20,
          }}>
            <div style={{ textAlign: 'center', minWidth: 100 }}>
              <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>Mgr Changes / Employee</div>
              <div style={{
                fontSize: 36, fontWeight: 700,
                color: analysis.manager_change_frequency > 1.5 ? '#ef4444'
                  : analysis.manager_change_frequency > 0.8 ? '#f59e0b' : '#10b981',
              }}>
                {analysis.manager_change_frequency.toFixed(1)}
              </div>
            </div>
            <div style={{ flex: 1, fontSize: 13, color: '#4b5563', lineHeight: 1.6 }}>
              {analysis.manager_change_frequency > 1.5
                ? 'High manager churn. Frequent manager changes correlate strongly with voluntary turnover. Stabilize leadership assignments where possible.'
                : analysis.manager_change_frequency > 0.8
                ? 'Moderate manager instability. Some teams are experiencing leadership transitions. Monitor for impact on engagement.'
                : 'Manager stability is healthy. Consistent leadership supports team cohesion and retention.'}
            </div>
          </div>
        </>
      )}

      {/* ===== EQUITY & MOBILITY TAB ===== */}
      {!loading && !error && analysis && activeTab === 'equity' && (
        <>
          {/* Top mobility stats */}
          <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
            <StatCard label="Internal Mobility Rate" value={`${analysis.internal_mobility_rate}%`} subtext="Transfers / headcount" />
            <StatCard label="Promotion Rate" value={`${analysis.promotion_rate}%`} subtext="Period" />
            <StatCard label="Mgr Change Freq" value={analysis.manager_change_frequency.toFixed(2)} subtext="Per employee" />
          </div>

          {/* Promotion equity chart */}
          <div style={{ marginBottom: 24 }}>
            <PromotionEquityChart data={analysis.promotion_equity} />
          </div>

          {/* Equity insight card */}
          {Object.keys(analysis.promotion_equity).length > 1 && (() => {
            const rates = Object.values(analysis.promotion_equity);
            const avg = rates.reduce((a, b) => a + b, 0) / rates.length;
            const flaggedDepts = Object.entries(analysis.promotion_equity).filter(
              ([, r]) => avg > 0 && (r < avg * 0.5 || r > avg * 2)
            );

            return flaggedDepts.length > 0 ? (
              <div style={{
                padding: 20, background: '#fef3c7', border: '1px solid #fcd34d',
                borderRadius: 12, marginBottom: 24,
              }}>
                <div style={{ fontWeight: 700, fontSize: 15, color: '#92400e', marginBottom: 8 }}>
                  Promotion Equity Alert
                </div>
                <div style={{ fontSize: 13, color: '#78350f', lineHeight: 1.6 }}>
                  {flaggedDepts.length} department{flaggedDepts.length > 1 ? 's' : ''} show{flaggedDepts.length === 1 ? 's' : ''} promotion
                  rates significantly different from the org average ({avg.toFixed(1)}%):
                  {' '}{flaggedDepts.map(([d, r]) => `${d} (${r.toFixed(1)}%)`).join(', ')}.
                  This may indicate systemic barriers or role structure differences worth investigating.
                </div>
              </div>
            ) : (
              <div style={{
                padding: 20, background: '#f0fdf4', border: '1px solid #86efac',
                borderRadius: 12, marginBottom: 24,
              }}>
                <div style={{ fontWeight: 700, fontSize: 15, color: '#166534', marginBottom: 4 }}>
                  Promotion Equity Healthy
                </div>
                <div style={{ fontSize: 13, color: '#14532d' }}>
                  No departments show promotion rates deviating more than 2x from the org average.
                </div>
              </div>
            );
          })()}

          {/* Internal mobility insight */}
          <div style={{
            padding: 20, background: '#fff', borderRadius: 12,
            border: '1px solid #e5e7eb',
          }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12, color: '#374151' }}>
              Internal Mobility Insight
            </div>
            <div style={{ fontSize: 13, color: '#4b5563', lineHeight: 1.6 }}>
              {analysis.internal_mobility_rate > 10
                ? 'High internal mobility indicates a healthy talent marketplace. Employees are finding growth opportunities within the organization, which reduces external attrition.'
                : analysis.internal_mobility_rate > 3
                ? 'Moderate internal mobility. There is some cross-team movement, but there may be room to improve internal career pathing and visibility of open roles.'
                : 'Low internal mobility. Employees may not see paths for growth beyond their current team. Consider internal job boards, rotation programs, or mentorship initiatives to increase movement.'}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default EmployeeLifecycleDashboard;
