/**
 * PsychSync Mobile - Main Entry Point
 *
 * React Native application for mental health assessments
 * and telehealth video consultations.
 */

import { AppRegistry } from 'react-native';
import App from './src/App';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
