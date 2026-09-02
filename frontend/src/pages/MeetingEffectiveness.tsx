import { useState } from 'react';

const TAGS = ['productive', 'good_decisions', 'no_agenda', 'too_long', 'wrong_people'];
const TAG_LABELS: Record<string, { label: string; color: string }> = {
  productive: { label: 'Productive', color: '#22c55e' },
  good_decisions: { label: 'Good Decisions', color: '#3b82f6' },
  no_agenda: { label: 'No Agenda', color: '#ef4444' },
  too_long: { label: 'Too Long', color: '#f97316' },
  wrong_people: { label: 'Wrong People', color: '#eab308' },
};

function MeetingEffectiveness() {
  const [score, setScore] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const handleSubmit = () => {
    // Placeholder — will wire to POST /api/v1/meeting-effectiveness/rate
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <div style={{ padding: 24, maxWidth: 800, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Meeting Effectiveness</h1>
      <p style={{ color: '#6b7280', marginBottom: 32 }}>
        Rate meetings to build organizational meeting health signals that feed into BI scoring.
      </p>

      {/* Rating section */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Rate Your Last Meeting</h2>

        {/* Star rating */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          {[1, 2, 3, 4, 5].map(n => (
            <button
              key={n}
              onClick={() => setScore(n)}
              style={{
                fontSize: 36,
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                filter: n <= score ? 'none' : 'grayscale(1) opacity(0.3)',
                transition: 'all 0.15s',
              }}
            >
              ⭐
            </button>
          ))}
          {score > 0 && <span style={{ alignSelf: 'center', fontSize: 14, color: '#6b7280' }}>{score}/5</span>}
        </div>

        {/* Tags */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>Tags (optional)</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {TAGS.map(tag => {
              const t = TAG_LABELS[tag];
              const selected = selectedTags.includes(tag);
              return (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 20,
                    border: `2px solid ${t.color}`,
                    background: selected ? t.color : 'transparent',
                    color: selected ? '#fff' : t.color,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  {t.label}
                </button>
              );
            })}
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={score === 0}
          style={{
            padding: '10px 24px',
            background: score > 0 ? '#4f46e5' : '#d1d5db',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: score > 0 ? 'pointer' : 'not-allowed',
            fontWeight: 600,
          }}
        >
          {submitted ? 'Submitted!' : 'Submit Rating'}
        </button>
      </div>

      {/* Org summary placeholder */}
      <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
        <h3 style={{ fontSize: 18, fontWeight: 600, color: '#374151' }}>Organization Meeting Health</h3>
        <p style={{ fontSize: 14, color: '#6b7280' }}>
          Meeting effectiveness scores are aggregated and fed into the Behavioral Intelligence team_health score at 15% weight.
        </p>
      </div>
    </div>
  );
}

export default MeetingEffectiveness;
