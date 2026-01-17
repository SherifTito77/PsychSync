/**
 * LSAS (Social Anxiety) Assessment Screen
 *
 * 24-item dual-rating assessment for social anxiety disorder.
 * Each item rates both fear and avoidance on 0-3 scale.
 *
 * SCORING:
 * - Fear score: Sum of fear ratings
 * - Avoidance score: Sum of avoidance ratings
 * - Total score: Fear + Avoidance (0-144)
 * - Clinical cutoffs:
 *   - < 30: Minimal
 *   - 30-49: Mild
 *   - 50-65: Moderate
 *   - 66-80: Marked
 *   - > 80: Severe
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Card, Button, ProgressBar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';
import api from '@services/api';
import { theme, assessmentTypes } from '@constants/theme';

interface LSASItem {
  item_number: number;
  fear: number;
  avoidance: number;
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

const LSASScreen: React.FC = ({ navigation }) => {
  const [responses, setResponses] = useState<LSASItem[]>(
    LSAS_ITEMS.map((_, index) => ({
      item_number: index + 1,
      fear: 0,
      avoidance: 0,
    }))
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentProgress = (responses.filter(r => r.fear > 0 && r.avoidance > 0).length / LSAS_ITEMS.length);

  const updateRating = (itemNumber: number, field: 'fear' | 'avoidance', value: number) => {
    setResponses(prev =>
      prev.map(item =>
        item.item_number === itemNumber
          ? { ...item, [field]: value }
          : item
      )
    );
  };

  const handleSubmit = async () => {
    // Validate all items completed
    const incomplete = responses.filter(r => r.fear === 0 || r.avoidance === 0);
    if (incomplete.length > 0) {
      Alert.alert('Incomplete Assessment', 'Please rate all items before submitting.');
      return;
    }

    setIsSubmitting(true);

    try {
      // Convert to API format
      const formattedResponses = responses.reduce((acc, item) => {
        acc[`item_${item.item_number}`] = {
          fear: item.fear,
          avoidance: item.avoidance,
        };
        return acc;
      }, {} as Record<string, { fear: number; avoidance: number }>);

      const response = await api.submitAssessment('LSAS', formattedResponses);

      Alert.alert(
        'Assessment Complete',
        `Your social anxiety level: ${response.data.severity_level}`,
        [
          {
            text: 'View Results',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to submit assessment. Please try again.');
      console.error('LSAS submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderRatingButtons = (itemNumber: number, field: 'fear' | 'avoidance') => {
    const currentValue = responses[itemNumber - 1][field];
    const labels = ['None', 'Mild', 'Moderate', 'Severe'];

    return (
      <View style={styles.ratingContainer}>
        <Text style={styles.ratingLabel}>{field === 'fear' ? 'Fear' : 'Avoidance'}:</Text>
        <View style={styles.ratingButtons}>
          {[0, 1, 2, 3].map(value => (
            <TouchableOpacity
              key={value}
              style={[
                styles.ratingButton,
                currentValue === value && styles.ratingButtonActive,
              ]}
              onPress={() => updateRating(itemNumber, field, value)}
            >
              <Text
                style={[
                  styles.ratingButtonText,
                  currentValue === value && styles.ratingButtonTextActive,
                ]}
              >
                {value}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.ratingHint}>
          {labels[currentValue]}
        </Text>
      </View>
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="psychology" size={48} color={theme.colors.primary} />
        <Text style={styles.title}>Social Anxiety Assessment</Text>
        <Text style={styles.subtitle}>Liebowitz Social Anxiety Scale (LSAS)</Text>
        <ProgressBar progress={currentProgress} style={styles.progressBar} />
        <Text style={styles.progressText}>
          {Math.round(currentProgress * 100)}% Complete
        </Text>
      </View>

      <View style={styles.content}>
        {LSAS_ITEMS.map((item, index) => (
          <Card key={index} style={styles.card}>
            <Card.Content>
              <Text style={styles.itemTitle}>
                {index + 1}. {item}
              </Text>

              <View style={styles.ratingsSection}>
                {renderRatingButtons(index + 1, 'fear')}
                <View style={styles.separator} />
                {renderRatingButtons(index + 1, 'avoidance')}
              </View>
            </Card.Content>
          </Card>
        ))}

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={isSubmitting}
          disabled={isSubmitting || currentProgress < 1}
          style={styles.submitButton}
          contentStyle={styles.submitButtonContent}
        >
          Submit Assessment
        </Button>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          This assessment is not a diagnosis. Consult a mental health professional.
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    padding: theme.spacing.lg,
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  title: {
    fontSize: theme.fontSizes.xxl,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginTop: theme.spacing.md,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: theme.fontSizes.md,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
    textAlign: 'center',
  },
  progressBar: {
    width: '100%',
    marginTop: theme.spacing.md,
    height: 8,
    borderRadius: 4,
  },
  progressText: {
    fontSize: theme.fontSizes.sm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  content: {
    padding: theme.spacing.md,
  },
  card: {
    marginBottom: theme.spacing.md,
    elevation: 2,
  },
  itemTitle: {
    fontSize: theme.fontSizes.md,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  ratingsSection: {
    marginTop: theme.spacing.sm,
  },
  ratingContainer: {
    marginVertical: theme.spacing.xs,
  },
  ratingLabel: {
    fontSize: theme.fontSizes.sm,
    fontWeight: '600',
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  ratingButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  ratingButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: theme.colors.surface,
    borderWidth: 2,
    borderColor: theme.colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ratingButtonActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  ratingButtonText: {
    fontSize: theme.fontSizes.lg,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  ratingButtonTextActive: {
    color: theme.colors.surface,
  },
  ratingHint: {
    fontSize: theme.fontSizes.xs,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
    textAlign: 'center',
  },
  separator: {
    height: 1,
    backgroundColor: theme.colors.border,
    marginVertical: theme.spacing.sm,
  },
  submitButton: {
    marginTop: theme.spacing.lg,
  },
  submitButtonContent: {
    paddingVertical: theme.spacing.sm,
  },
  footer: {
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.warning + '20',
    borderTopWidth: 1,
    borderTopColor: theme.colors.warning,
  },
  footerText: {
    fontSize: theme.fontSizes.sm,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
});

export default LSASScreen;
