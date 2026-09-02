import { useState } from 'react';

interface NewHireHealth {
  user_id: string;
  name: string;
  hire_date: string;
  tenure_days: number;
  health_score: number;
  signals: {
    network_velocity: number;
    recognition_received: number;
    platform_engagement: number;
    wellness_baseline: number;
  };
}

function healthColor(score: number): string {
  if (score >= 70) return '#22c55e';
  if (score >= 40) return '#eab308';
  return '#ef4444';
}

function OnboardingAnalytics() {
  const [newHires] = useState<NewHireHealth[]>([]);
  const [windowDays, setWindowDays] = useState(90);

  const signalLabels: Record<string, { label: string; icon: string; weight: string }> = {
    network_velocity: { label: 'Network Velocity', icon: '🕸', weight: '35%' },
    platform_engagement: { label: 'Platform Engagement', icon: '📱', weight: '25%' },
    recognition_received: { label: 'Recognition Received', icon: '🏆', weight: '20%' },
    wellness_baseline: { label: 'Wellness Baseline', icon: '💚', weight: '20%' },
  };

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Onboarding Analytics</h1>
          <p style={{ color: '#6b7280' }}>
            Track new hire health using existing signals — no new surveys needed.
          </p>
        </div>
        <select
          value={windowDays}
          onChange={e => setWindowDays(Number(e.target.value))}
          style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}
        >
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
          <option value={180}>Last 180 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {/* Signal explanation */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 32 }}>
        {Object.entries(signalLabels).map(([key, sig]) => (
          <div key={key} style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>{sig.icon}</div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{sig.label}</div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>Weight: {sig.weight}</div>
          </div>
        ))}
      </div>

      {/* New hires list */}
      {newHires.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#9ca3af', background: '#f9fafb', borderRadius: 12 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>👋</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: '#374151' }}>No new hires in window</h3>
          <p style={{ fontSize: 14 }}>
            Users who joined within the last {windowDays} days will appear here with their health composite.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {newHires.map(hire => (
            <div key={hire.user_id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: healthColor(hire.health_score), color: '#fff', fontWeight: 700, fontSize: 16,
              }}>
                {Math.round(hire.health_score)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{hire.name}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Day {hire.tenure_days} &middot; Hired {hire.hire_date}</div>
              </div>
              {Object.entries(hire.signals).map(([key, val]) => (
                <div key={key} style={{ textAlign: 'center', minWidth: 60 }}>
                  <div style={{ fontSize: 16, fontWeight: 600, color: healthColor(val) }}>{Math.round(val)}</div>
                  <div style={{ fontSize: 10, color: '#9ca3af' }}>{signalLabels[key]?.icon}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default OnboardingAnalytics;
