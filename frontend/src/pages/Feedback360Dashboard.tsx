import { useState } from 'react';

interface FeedbackRound {
  id: string;
  title: string;
  status: string;
  created_at: string;
  total_requests: number;
  completed_responses: number;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  draft: { bg: '#f3f4f6', text: '#6b7280' },
  active: { bg: '#dbeafe', text: '#1d4ed8' },
  closed: { bg: '#dcfce7', text: '#15803d' },
};

function Feedback360Dashboard() {
  const [rounds] = useState<FeedbackRound[]>([]);

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>360 Feedback</h1>
      <p style={{ color: '#6b7280', marginBottom: 24 }}>
        Multi-rater feedback campaigns with privacy-safe aggregation and blind spot detection.
      </p>

      {/* Key concepts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 24, marginBottom: 4 }}>🔒</div>
          <div style={{ fontWeight: 600, fontSize: 14 }}>Privacy-Safe</div>
          <div style={{ fontSize: 12, color: '#6b7280' }}>Results suppressed when rater group &lt; minimum threshold</div>
        </div>
        <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 24, marginBottom: 4 }}>🎯</div>
          <div style={{ fontWeight: 600, fontSize: 14 }}>Blind Spot Detection</div>
          <div style={{ fontSize: 12, color: '#6b7280' }}>Identifies gaps between self-assessment and others' ratings</div>
        </div>
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 24, marginBottom: 4 }}>📊</div>
          <div style={{ fontWeight: 600, fontSize: 14 }}>5 Rater Categories</div>
          <div style={{ fontSize: 12, color: '#6b7280' }}>Self, Manager, Peer, Direct Report, Stakeholder</div>
        </div>
      </div>

      {/* Rounds list */}
      {rounds.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#9ca3af', background: '#f9fafb', borderRadius: 12 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🔄</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: '#374151' }}>No feedback rounds yet</h3>
          <p style={{ fontSize: 14 }}>Create a feedback round to start collecting multi-rater assessments.</p>
          <button style={{ marginTop: 16, padding: '10px 20px', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}>
            + Create Round
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {rounds.map(round => {
            const sc = STATUS_COLORS[round.status] || STATUS_COLORS.draft;
            const completion = round.total_requests > 0
              ? Math.round((round.completed_responses / round.total_requests) * 100)
              : 0;
            return (
              <div key={round.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{round.title}</div>
                  <div style={{ fontSize: 12, color: '#6b7280' }}>{round.created_at}</div>
                </div>
                <div style={{ width: 100, background: '#e5e7eb', borderRadius: 4, height: 6, marginRight: 12 }}>
                  <div style={{ width: `${completion}%`, background: '#4f46e5', borderRadius: 4, height: 6 }} />
                </div>
                <span style={{ fontSize: 12, color: '#6b7280' }}>{completion}%</span>
                <span style={{ background: sc.bg, color: sc.text, padding: '4px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
                  {round.status.toUpperCase()}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Feedback360Dashboard;
