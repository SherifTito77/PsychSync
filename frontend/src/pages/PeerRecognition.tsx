import { useState, useEffect, useCallback } from 'react';
import {
  getReceivedRecognitions,
  getRecognitionStats,
  type Recognition,
  type RecognitionStats,
} from '../services/recognitionService';

const RECOGNITION_TYPES = [
  { value: 'thank_you', label: 'Thank You', emoji: '🙏' },
  { value: 'great_work', label: 'Great Work', emoji: '⭐' },
  { value: 'innovation', label: 'Innovation', emoji: '💡' },
  { value: 'teamwork', label: 'Teamwork', emoji: '🤝' },
  { value: 'leadership', label: 'Leadership', emoji: '🎯' },
  { value: 'mentorship', label: 'Mentorship', emoji: '📚' },
  { value: 'above_and_beyond', label: 'Above & Beyond', emoji: '🚀' },
];

function typeInfo(value: string) {
  return RECOGNITION_TYPES.find((t) => t.value === value) || { label: value, emoji: '⭐' };
}

function StatCard({ value, label, color }: { value: number | string; label: string; color: string }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 12, padding: 20,
      border: '1px solid #e5e7eb', textAlign: 'center',
    }}>
      <div style={{ fontSize: 32, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>{label}</div>
    </div>
  );
}

function TypeBreakdown({ breakdown }: { breakdown: Record<string, number> }) {
  const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);
  const max = entries.length > 0 ? entries[0][1] : 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {entries.map(([type, count]) => {
        const info = typeInfo(type);
        return (
          <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 20, width: 28 }}>{info.emoji}</span>
            <span style={{ width: 120, fontSize: 14 }}>{info.label}</span>
            <div style={{ flex: 1, height: 20, borderRadius: 10, background: '#f3f4f6', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 10,
                width: `${(count / max) * 100}%`,
                background: 'linear-gradient(90deg, #8b5cf6, #a78bfa)',
                transition: 'width 0.5s',
              }} />
            </div>
            <span style={{ width: 32, textAlign: 'right', fontSize: 14, fontWeight: 600 }}>{count}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function PeerRecognition() {
  const [activeTab, setActiveTab] = useState<'received' | 'stats'>('received');
  const [recognitions, setRecognitions] = useState<Recognition[]>([]);
  const [stats, setStats] = useState<RecognitionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchReceived = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getReceivedRecognitions(90);
      setRecognitions(data.recognitions);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load recognitions');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const orgId = localStorage.getItem('organization_id') || '';
      if (!orgId) {
        setError('No organization selected');
        setLoading(false);
        return;
      }
      const data = await getRecognitionStats(orgId, 90);
      setStats(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'received') fetchReceived();
    else fetchStats();
  }, [activeTab, fetchReceived, fetchStats]);

  const tabs = [
    { key: 'received' as const, label: 'My Recognitions' },
    { key: 'stats' as const, label: 'Organization Stats' },
  ];

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Peer Recognition</h1>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '2px solid #e5e7eb' }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 20px', border: 'none', cursor: 'pointer',
              background: activeTab === tab.key ? '#fff' : 'transparent',
              borderBottom: activeTab === tab.key ? '2px solid #8b5cf6' : '2px solid transparent',
              color: activeTab === tab.key ? '#8b5cf6' : '#6b7280',
              fontWeight: activeTab === tab.key ? 600 : 400,
              fontSize: 14, marginBottom: -2,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 48, color: '#6b7280' }}>Loading...</div>}
      {error && <div style={{ textAlign: 'center', padding: 48, color: '#ef4444' }}>{error}</div>}

      {/* Received Tab */}
      {!loading && !error && activeTab === 'received' && (
        <div>
          {recognitions.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: 48, color: '#6b7280',
              background: '#fff', borderRadius: 12, border: '1px solid #e5e7eb',
            }}>
              No recognitions received yet. Recognitions from your peers will appear here.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {recognitions.map((rec) => {
                const info = typeInfo(rec.type);
                return (
                  <div
                    key={rec.id}
                    style={{
                      background: '#fff', borderRadius: 12, padding: 16,
                      border: '1px solid #e5e7eb', display: 'flex', gap: 16, alignItems: 'flex-start',
                    }}
                  >
                    <span style={{
                      fontSize: 28, width: 48, height: 48, display: 'flex',
                      alignItems: 'center', justifyContent: 'center',
                      background: '#f5f3ff', borderRadius: 12,
                    }}>
                      {info.emoji}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, marginBottom: 4 }}>{info.label}</div>
                      {rec.message && (
                        <div style={{ fontSize: 14, color: '#4b5563', lineHeight: 1.5 }}>
                          "{rec.message}"
                        </div>
                      )}
                      <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>
                        {new Date(rec.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Stats Tab */}
      {!loading && !error && activeTab === 'stats' && stats && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
            <StatCard value={stats.total_recognitions} label="Total Recognitions" color="#8b5cf6" />
            <StatCard value={stats.unique_givers} label="Unique Givers" color="#3b82f6" />
            <StatCard value={stats.unique_receivers} label="Unique Receivers" color="#22c55e" />
          </div>

          <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e5e7eb' }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: 16, fontWeight: 600 }}>Recognition Types</h3>
            {Object.keys(stats.type_breakdown).length === 0 ? (
              <div style={{ textAlign: 'center', padding: 24, color: '#6b7280' }}>
                No recognition data yet for this period.
              </div>
            ) : (
              <TypeBreakdown breakdown={stats.type_breakdown} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
