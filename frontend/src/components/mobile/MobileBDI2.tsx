/**
 * Mobile BDI-II (Beck Depression Inventory-II)
 *
 * Mobile-optimized version of the BDI-II assessment
 * 21 questions, 0-3 scale per question
 * Total score range: 0-63
 *
 * Features:
 * - One question per screen
 * - Large touch targets (60px min height)
 * - Swipe navigation
 * - Progress indicator
 * - Auto-advance on selection
 */

import React from 'react';
import api from '@/services/api';
import { MobileAssessmentWizard } from './MobileAssessmentWizard';

// BDI-II Questions (21 items)
const BDI2_QUESTIONS = [
  {
    id: '1',
    text: 'Sadness',
    options: [
      { value: 0, text: 'I do not feel sad' },
      { value: 1, text: 'I feel sad much of the time' },
      { value: 2, text: 'I am sad all the time' },
      { value: 3, text: "I am so sad or unhappy that I can't stand it" },
    ],
    category: 'Affective',
  },
  {
    id: '2',
    text: 'Pessimism',
    options: [
      { value: 0, text: 'I am not discouraged about my future' },
      { value: 1, text: 'I feel more discouraged about my future than I used to be' },
      { value: 2, text: 'I do not expect things to work out for me' },
      { value: 3, text: 'I feel my future is hopeless and will only get worse' },
    ],
    category: 'Cognitive',
  },
  {
    id: '3',
    text: 'Past Failure',
    options: [
      { value: 0, text: 'I do not feel like a failure' },
      { value: 1, text: 'I have failed more than I should have' },
      { value: 2, text: 'As I look back, I see a lot of failures' },
      { value: 3, text: 'I feel I am a total failure as a person' },
    ],
    category: 'Cognitive',
  },
  {
    id: '4',
    text: 'Loss of Pleasure',
    options: [
      { value: 0, text: 'I get as much pleasure as I ever did from things I enjoy' },
      { value: 1, text: "I don't enjoy things as much as I used to" },
      { value: 2, text: 'I get very little pleasure from things I used to enjoy' },
      { value: 3, text: "I can't get any pleasure from things I used to enjoy" },
    ],
    category: 'Affective',
  },
  {
    id: '5',
    text: 'Guilty Feelings',
    options: [
      { value: 0, text: "I don't feel particularly guilty" },
      { value: 1, text: 'I feel guilty a good part of the time' },
      { value: 2, text: 'I feel quite guilty most of the time' },
      { value: 3, text: 'I feel guilty all of the time' },
    ],
    category: 'Cognitive',
  },
  {
    id: '6',
    text: 'Punishment Feelings',
    options: [
      { value: 0, text: "I don't feel I am being punished" },
      { value: 1, text: 'I feel I may be punished' },
      { value: 2, text: 'I expect to be punished' },
      { value: 3, text: 'I feel I am being punished' },
    ],
    category: 'Cognitive',
  },
  {
    id: '7',
    text: 'Self-Dislike',
    options: [
      { value: 0, text: 'I feel the same about myself as ever' },
      { value: 1, text: 'I have lost confidence in myself' },
      { value: 2, text: 'I am disappointed in myself' },
      { value: 3, text: 'I dislike myself' },
    ],
    category: 'Cognitive',
  },
  {
    id: '8',
    text: 'Self-Criticalness',
    options: [
      { value: 0, text: "I don't criticize or blame myself more than usual" },
      { value: 1, text: 'I am more critical of myself than I used to be' },
      { value: 2, text: 'I criticize myself for all of my faults' },
      { value: 3, text: 'I blame myself for everything bad that happens' },
    ],
    category: 'Cognitive',
  },
  {
    id: '9',
    text: 'Suicidal Thoughts or Wishes',
    options: [
      { value: 0, text: "I don't have any thoughts of killing myself" },
      { value: 1, text: 'I have thoughts of killing myself, but I would not carry them out' },
      { value: 2, text: 'I would like to kill myself' },
      { value: 3, text: 'I would kill myself if I had the chance' },
    ],
    category: 'Cognitive',
  },
  {
    id: '10',
    text: 'Crying',
    options: [
      { value: 0, text: "I don't cry any more than I used to" },
      { value: 1, text: 'I cry more than I used to' },
      { value: 2, text: 'I cry over every little thing' },
      { value: 3, text: "I feel like crying, but I can't" },
    ],
    category: 'Affective',
  },
  {
    id: '11',
    text: 'Agitation',
    options: [
      { value: 0, text: 'I am no more restless or wound up than usual' },
      { value: 1, text: 'I feel more restless or wound up than usual' },
      { value: 2, text: 'I am so restless or agitated, I can\'t sit still' },
      { value: 3, text: 'I am so restless or agitated that I have to keep moving or doing something' },
    ],
    category: 'Somatic',
  },
  {
    id: '12',
    text: 'Loss of Interest',
    options: [
      { value: 0, text: 'I have not lost interest in other people or activities' },
      { value: 1, text: 'I am less interested in other people or things than before' },
      { value: 2, text: 'I have lost most of my interest in other people or things' },
      { value: 3, text: "It's hard to get interested in anything" },
    ],
    category: 'Affective',
  },
  {
    id: '13',
    text: 'Indecisiveness',
    options: [
      { value: 0, text: 'I make decisions about as well as ever' },
      { value: 1, text: 'I find it more difficult to make decisions than usual' },
      { value: 2, text: 'I have much greater difficulty in making decisions than I used to' },
      { value: 3, text: "I can't make decisions at all anymore" },
    ],
    category: 'Cognitive',
  },
  {
    id: '14',
    text: 'Worthlessness',
    options: [
      { value: 0, text: 'I do not feel I am worthless' },
      { value: 1, text: "I don't consider myself as worthwhile and useful as I used to" },
      { value: 2, text: 'I feel I am not very worthwhile' },
      { value: 3, text: 'I feel completely worthless' },
    ],
    category: 'Cognitive',
  },
  {
    id: '15',
    text: 'Loss of Energy',
    options: [
      { value: 0, text: 'I have as much energy as ever' },
      { value: 1, text: 'I have less energy than I used to have' },
      { value: 2, text: "I don't have enough energy to do very much" },
      { value: 3, text: "I don't have enough energy to do anything" },
    ],
    category: 'Somatic',
  },
  {
    id: '16',
    text: 'Changes in Sleeping Pattern',
    options: [
      { value: 0, text: 'I have not experienced any change in my sleeping' },
      { value: 1, text: 'I sleep somewhat more or less than usual' },
      { value: 2, text: 'I sleep a lot more or a lot less than usual' },
      { value: 3, text: 'I sleep most of the day or can\'t sleep at all' },
    ],
    category: 'Somatic',
  },
  {
    id: '17',
    text: 'Irritability',
    options: [
      { value: 0, text: 'I am not more irritable than usual' },
      { value: 1, text: 'I am more irritable than usual' },
      { value: 2, text: 'I am much more irritable than usual' },
      { value: 3, text: 'I am irritable all the time' },
    ],
    category: 'Somatic',
  },
  {
    id: '18',
    text: 'Changes in Appetite',
    options: [
      { value: 0, text: 'I have not experienced any change in my appetite' },
      { value: 1, text: 'My appetite is somewhat less or greater than usual' },
      { value: 2, text: 'My appetite is much less or much greater than usual' },
      { value: 3, text: 'I have no appetite at all or can\'t stop eating' },
    ],
    category: 'Somatic',
  },
  {
    id: '19',
    text: 'Concentration Difficulty',
    options: [
      { value: 0, text: 'I can concentrate as well as ever' },
      { value: 1, text: "I can't concentrate as well as usual" },
      { value: 2, text: "It's hard to keep my mind on anything for very long" },
      { value: 3, text: "I find I can't concentrate on anything" },
    ],
    category: 'Cognitive',
  },
  {
    id: '20',
    text: 'Tiredness or Fatigue',
    options: [
      { value: 0, text: 'I am no more tired or fatigued than usual' },
      { value: 1, text: 'I get more tired or fatigued more easily than usual' },
      { value: 2, text: 'I am too tired or fatigued to do a lot of the things I used to do' },
      { value: 3, text: 'I am too tired or fatigued to do most of the things I used to do' },
    ],
    category: 'Somatic',
  },
  {
    id: '21',
    text: 'Loss of Interest in Sex',
    options: [
      { value: 0, text: 'I have not noticed any recent change in my interest in sex' },
      { value: 1, text: 'I am less interested in sex than I used to be' },
      { value: 2, text: 'I am much less interested in sex now' },
      { value: 3, text: 'I have lost interest in sex completely' },
    ],
    category: 'Somatic',
  },
];

export function MobileBDI2() {
  const handleSubmit = async (responses: Record<string, number>) => {
    const response = await api.post('/clinical/BDI2/submit', responses);
    return response.data as void;
  };

  return (
    <MobileAssessmentWizard
      title="Beck Depression Inventory-II"
      description="This assessment measures depression severity. Please answer each question based on how you've been feeling during the past two weeks, including today."
      questions={BDI2_QUESTIONS}
      onSubmit={handleSubmit}
      submitEndpoint="/api/v1/clinical/BDI2/submit"
      showCategory={true}
    />
  );
}

export default MobileBDI2;
