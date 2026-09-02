import { useState } from 'react';

interface NudgeResult {
  type: string;
  sent: number;
  icon: string;
  description: string;
}

const NUDGE_TYPES: NudgeResult[] = [
  { type: 'pulse_survey', sent: 0, icon: '📋', description: 'Remind non-respondents to complete pulse surveys' },
  { type: 'burnout_wellness', sent: 0, icon: '🧘', description: 'Gentle wellness nudges for users with elevated burnout signals' },
  { type: 'action_plan', sent: 0, icon: '📋', description: 'Remind owners of overdue or upcoming action plans' },
  { type: 'recognition', sent: 0, icon: '🏆', description: 'Prompt users who haven\'t given recognition recently' },
  { type: 'okr_checkin', sent: 0, icon: '🎯', description: 'Remind OKR owners to update their key results' },
];

function NudgeBotDashboard() {
  const [nudgeTypes] = useState(NUDGE_TYPES);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState<string | null>(null);

  const handleRunAll = async () => {
    setRunning(true);
    // Placeholder — will wire to POST /api/v1/nudge-bot/{org_id}/run-all
    setTimeout(() => {
      setRunning(false);
      setLastRun(new Date().toLocaleString());
    }, 2000);
  };

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Nudge Bot</h1>
          <p style={{ color: '#6b7280' }}>
            Proactive outbound nudges via Slack/Teams. Typically triggered by external cron.
          </p>
          {lastRun && <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>Last run: {lastRun}</p>}
        </div>
        <button
          onClick={handleRunAll}
          disabled={running}
          style={{
            padding: '10px 20px',
            background: running ? '#9ca3af' : '#4f46e5',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: running ? 'not-allowed' : 'pointer',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          {running ? 'Running...' : '🚀 Run All Nudges'}
        </button>
      </div>

      {/* Nudge types grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {nudgeTypes.map(nudge => (
          <div
            key={nudge.type}
            style={{
              background: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: 12,
              padding: 20,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div style={{ fontSize: 36 }}>{nudge.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, marginBottom: 2, textTransform: 'capitalize' }}>
                {nudge.type.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: 13, color: '#6b7280' }}>{nudge.description}</div>
            </div>
            <div style={{ textAlign: 'center', minWidth: 60 }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: nudge.sent > 0 ? '#4f46e5' : '#d1d5db' }}>
                {nudge.sent}
              </div>
              <div style={{ fontSize: 11, color: '#9ca3af' }}>sent</div>
            </div>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div style={{ marginTop: 32, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 12, padding: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>How Nudge Bot Works</h3>
        <ul style={{ fontSize: 13, color: '#374151', lineHeight: 1.8, paddingLeft: 20 }}>
          <li>Nudges are sent via Slack Direct Message with Block Kit formatting</li>
          <li>Each nudge includes an action button linking to the relevant page</li>
          <li>Delivery failures are logged but never block the calling service</li>
          <li>Typically called by an external cron job (e.g., daily at 9am)</li>
          <li>Recognition prompts are capped at 50 per run to prevent spam</li>
        </ul>
      </div>
    </div>
  );
}

export default NudgeBotDashboard;
