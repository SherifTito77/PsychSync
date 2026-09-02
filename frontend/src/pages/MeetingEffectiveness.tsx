import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface MeetingSummary {
  total_ratings: number;
  avg_score: number;
  tag_frequency: Record<string, number>;
  team_summaries?: Array<{ team_id: string; avg_score: number; count: number }>;
}

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
  const [submitting, setSubmitting] = useState(false);
  const [summary, setSummary] = useState<MeetingSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = 'current';

  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const res = await axios.get(`/api/v1/meeting-effectiveness/summary/${orgId}`);
      setSummary(res.data);
    } catch {
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await axios.post('/api/v1/meeting-effectiveness/rate', {
        score,
        tags: selectedTags,
        meeting_id: null,
      });
      setSubmitted(true);
      setScore(0);
      setSelectedTags([]);
      await fetchSummary();
      setTimeout(() => setSubmitted(false), 3000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to submit rating');
    } finally {
      setSubmitting(false);
    }
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

        {error && (
          <div style={{
            padding: 12, background: '#fef2f2', border: '1px solid #fecaca',
            borderRadius: 8, color: '#991b1b', marginBottom: 12, fontSize: 13,
          }}>
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={score === 0 || submitting}
          style={{
            padding: '10px 24px',
            background: score > 0 && !submitting ? '#4f46e5' : '#d1d5db',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: score > 0 && !submitting ? 'pointer' : 'not-allowed',
            fontWeight: 600,
          }}
        >
          {submitting ? 'Submitting...' : submitted ? 'Submitted!' : 'Submit Rating'}
        </button>
      </div>

      {/* Org summary */}
      {summaryLoading ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#9ca3af' }}>Loading summary...</div>
      ) : summary && summary.total_ratings > 0 ? (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: '#374151' }}>Organization Meeting Health</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16, marginBottom: 20 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 36, fontWeight: 700, color: summary.avg_score >= 3.5 ? '#22c55e' : summary.avg_score >= 2.5 ? '#eab308' : '#ef4444' }}>
                {summary.avg_score.toFixed(1)}
              </div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>Avg Score (out of 5)</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 36, fontWeight: 700, color: '#4f46e5' }}>{summary.total_ratings}</div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>Total Ratings</div>
            </div>
          </div>
          {Object.keys(summary.tag_frequency).length > 0 && (
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: '#374151' }}>Tag Frequency</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {Object.entries(summary.tag_frequency).sort(([, a], [, b]) => b - a).map(([tag, count]) => {
                  const t = TAG_LABELS[tag];
                  return (
                    <span key={tag} style={{ padding: '4px 12px', borderRadius: 16, background: t?.color || '#6b7280', color: '#fff', fontSize: 12, fontWeight: 600 }}>
                      {t?.label || tag}: {count}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
          <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 16 }}>
            Meeting effectiveness scores feed into the Behavioral Intelligence team_health score at 15% weight.
          </p>
        </div>
      ) : (
        <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: '#374151' }}>Organization Meeting Health</h3>
          <p style={{ fontSize: 14, color: '#6b7280' }}>
            No ratings yet. Submit your first meeting rating above to start building organizational meeting health signals.
          </p>
        </div>
      )}
    </div>
  );
}

export default MeetingEffectiveness;
