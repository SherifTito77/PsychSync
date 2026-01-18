/**
 * LSAS (Liebowitz Social Anxiety Scale) Form Component
 *
 * 24-item dual-rating assessment measuring fear and avoidance
 * of social situations.
 *
 * CLINICAL VALIDITY:
 * - Reliability: α = 0.85-0.93
 * - Test-retest: r = 0.80-0.90
 * - Concurrent validity with other anxiety measures
 *
 * SCORING:
 * - Fear score: Sum of fear ratings (0-72)
 * - Avoidance score: Sum of avoidance ratings (0-72)
 * - Total score: Fear + Avoidance (0-144)
 *
 * CLINICAL CUTOFFS:
 * - < 30: Minimal social anxiety
 * - 30-49: Mild social anxiety
 * - 50-65: Moderate social anxiety
 * - 66-80: Marked social anxiety
 * - > 80: Severe social anxiety
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  RadioGroup,
  FormControlLabel,
  Radio,
  Button,
  Alert,
  LinearProgress,
  Stack,
  Divider,
  AlertTitle,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import PsychologyIcon from '@mui/icons-material/Psychology';
import axios from 'axios';
import { useError } from '../../contexts/ErrorContext';
import { handleError } from '../../utils/errorHandler';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface LSASItem {
  item_number: number;
  fear: number;
  avoidance: number;
}

interface LSASResponse {
  assessment_type: string;
  total_score: number;
  severity_level: string;
  risk_level: string;
  subscale_scores: {
    fear: number;
    avoidance: number;
  };
  interpretation: string;
  recommendations: string[];
  crisis_alert: boolean;
  risk_flags: string[];
  completed_at: string;
}

const LSAS_ITEMS = [
  'Using a telephone in public',
  'Participating in a small group',
  'Eating in public places',
  'Drinking with others in public places',
  'Talking to people in authority',
  'Acting, performing, or giving a talk in front of an audience',
  'Going to a party',
  'Working while being observed',
  'Writing while being observed',
  'Calling someone you don\'t know very well',
  'Talking with people you don\'t know very well',
  'Meeting strangers',
  'Urinating in a public bathroom',
  'Entering a room when others are already seated',
  'Being the center of attention',
  'Speaking up at a meeting',
  'Taking a test of your ability, skill, or knowledge',
  'Expressing disagreement or disapproval to people you don\'t know very well',
  'Looking people you don\'t know very well in the eye',
  'Giving a report to a group',
  'Trying to pick up someone',
  'Returning goods to a store',
  'Giving a party',
  'Resisting a high-pressure salesperson',
];

const RATING_LABELS = {
  0: 'None',
  1: 'Mild',
  2: 'Moderate',
  3: 'Severe',
};

const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4],
  },
}));

const RatingButton = styled(Button)<{ selected: boolean }>(({ selected, theme }) => ({
  minWidth: 60,
  height: 40,
  ...(selected && {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
    },
  }),
}));

const LSASForm: React.FC = () => {
  const { showError, showSuccess } = useError();
  const [responses, setResponses] = useState<LSASItem[]>(
    LSAS_ITEMS.map((_, index) => ({
      item_number: index + 1,
      fear: 0,
      avoidance: 0,
    }))
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LSASResponse | null>(null);

  const completedCount = responses.filter(
    (r) => r.fear > 0 && r.avoidance > 0
  ).length;
  const progress = completedCount / LSAS_ITEMS.length;

  const handleRatingChange = (
    itemNumber: number,
    field: 'fear' | 'avoidance',
    value: number
  ) => {
    setResponses((prev) =>
      prev.map((item) =>
        item.item_number === itemNumber
          ? { ...item, [field]: value }
          : item
      )
    );
  };

  const handleSubmit = async () => {
    // Validate all items completed
    const incomplete = responses.filter(
      (r) => r.fear === 0 || r.avoidance === 0
    );
    if (incomplete.length > 0) {
      setError('Please complete all ratings before submitting.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Format for API
      const formattedResponses = responses.reduce(
        (acc, item) => {
          acc[`item_${item.item_number}`] = {
            fear: item.fear,
            avoidance: item.avoidance,
          };
          return acc;
        },
        {} as Record<string, { fear: number; avoidance: number }>
      );

      const token = localStorage.getItem('access_token');
      const response = await axios.post<LSASResponse>(
        `${API_BASE}/clinical/LSAS/submit`,
        { responses: formattedResponses },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      setResult(response.data);

      // Show success notification
      showSuccess('Assessment submitted successfully! Your results are ready.');

      // Scroll to top to show results
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      // Handle error with user-friendly message
      const errorInfo = handleError(err, 'Submit LSAS assessment');
      const errorMessage = errorInfo.userMessage;

      setError(errorMessage);

      // Show error toast with retry option
      showError(errorMessage, {
        retryable: errorInfo.retryable,
        onRetry: errorInfo.retryable ? handleSubmit : undefined,
      });

      console.error('LSAS submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSeverityColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'minimal':
        return 'success';
      case 'mild':
        return 'info';
      case 'moderate':
        return 'warning';
      case 'marked':
        return 'error';
      case 'severe':
        return 'error';
      default:
        return 'info';
    }
  };

  if (result) {
    return (
      <Box maxWidth={800} mx="auto" p={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={3}>
              <PsychologyIcon
                sx={{ fontSize: 48, mr: 2, color: 'primary.main' }}
              />
              <Box>
                <Typography variant="h4" gutterBottom>
                  Assessment Complete
                </Typography>
                <Typography variant="body1" color="textSecondary">
                  Liebowitz Social Anxiety Scale (LSAS)
                </Typography>
              </Box>
            </Box>

            <Alert severity={getSeverityColor(result.severity_level)} sx={{ mb: 3 }}>
              <Typography variant="h6">
                Social Anxiety Level: {result.severity_level}
              </Typography>
              <Typography variant="body2">
                Total Score: {result.total_score} / 144
              </Typography>
            </Alert>

            {result.crisis_alert && (
              <Alert severity="error" sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  ⚠️ Crisis Alert Detected
                </Typography>
                <Typography variant="body2">
                  Your responses indicate significant distress. Please
                  consider reaching out to a mental health professional
                  or crisis resources:
                </Typography>
                <Box mt={2}>
                  <Typography variant="body2">
                    • National Suicide Prevention Lifeline: 988
                  </Typography>
                  <Typography variant="body2">
                    • Crisis Text Line: Text HOME to 741741
                  </Typography>
                </Box>
              </Alert>
            )}

            <Stack spacing={2} mt={3}>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Subscale Scores
                </Typography>
                <Typography variant="body2">
                  Fear Score: {result.subscale_scores.fear} / 72
                </Typography>
                <Typography variant="body2">
                  Avoidance Score: {result.subscale_scores.avoidance} / 72
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" gutterBottom>
                  Interpretation
                </Typography>
                <Typography variant="body2">
                  {result.interpretation}
                </Typography>
              </Box>

              {result.recommendations.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Recommendations
                  </Typography>
                  {result.recommendations.map((rec, index) => (
                    <Typography key={index} variant="body2" gutterBottom>
                      • {rec}
                    </Typography>
                  ))}
                </Box>
              )}
            </Stack>

            <Box mt={4}>
              <Button
                variant="contained"
                onClick={() => {
                  setResult(null);
                  setResponses(
                    LSAS_ITEMS.map((_, index) => ({
                      item_number: index + 1,
                      fear: 0,
                      avoidance: 0,
                    }))
                  );
                }}
              >
                Take Assessment Again
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box maxWidth={900} mx="auto" p={3}>
      {/* Header */}
      <Box textAlign="center" mb={4}>
        <PsychologyIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h3" gutterBottom>
          Social Anxiety Assessment
        </Typography>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          Liebowitz Social Anxiety Scale (LSAS)
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          For each situation, rate BOTH your fear and avoidance
        </Typography>

        <Box sx={{ width: '100%', mt: 3 }}>
          <LinearProgress
            variant="determinate"
            value={progress * 100}
            sx={{ height: 10, borderRadius: 5 }}
          />
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            {Math.round(progress * 100)}% Complete ({completedCount} of{' '}
            {LSAS_ITEMS.length} items)
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Assessment Items */}
      <Stack spacing={3}>
        {LSAS_ITEMS.map((item, index) => (
          <StyledCard key={index}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {index + 1}. {item}
              </Typography>

              <Grid container spacing={3}>
                {/* Fear Rating */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                    Fear:
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {[0, 1, 2, 3].map((value) => (
                      <RatingButton
                        key={value}
                        variant={responses[index].fear === value ? 'contained' : 'outlined'}
                        selected={responses[index].fear === value}
                        onClick={() => handleRatingChange(index + 1, 'fear', value)}
                      >
                            {value}
                      </RatingButton>
                    ))}
                  </Stack>
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                    {RATING_LABELS[responses[index].fear as keyof typeof RATING_LABELS]}
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                </Grid>

                {/* Avoidance Rating */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                    Avoidance:
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {[0, 1, 2, 3].map((value) => (
                      <RatingButton
                        key={value}
                        variant={responses[index].avoidance === value ? 'contained' : 'outlined'}
                        selected={responses[index].avoidance === value}
                        onClick={() => handleRatingChange(index + 1, 'avoidance', value)}
                      >
                        {value}
                      </RatingButton>
                    ))}
                  </Stack>
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                    {RATING_LABELS[responses[index].avoidance as keyof typeof RATING_LABELS]}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </StyledCard>
        ))}
      </Stack>

      {/* Submit Button */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={isSubmitting || progress < 1}
          sx={{ minWidth: 200, py: 1.5 }}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Assessment'}
        </Button>

        <Box sx={{ mt: 3, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
          <Typography variant="body2" color="textSecondary">
            <strong>Disclaimer:</strong> This assessment is not a diagnosis.
            Only a qualified mental health professional can diagnose social
            anxiety disorder. Please consult with a healthcare provider.
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default LSASForm;
