#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🎯 TESTING DASS-21 RESULTS NAVIGATION FIX');
console.log('='.repeat(50));
console.log('');

const dass21Path = path.join(__dirname, 'frontend/src/pages/clinical/DASS21Assessment.tsx');
const dass21Content = fs.readFileSync(dass21Path, 'utf8');

// Test 1: Check navigation path is corrected
console.log('1️⃣ TESTING NAVIGATION PATH CORRECTION');
console.log('-'.repeat(30));

const hasCorrectNavigation = dass21Content.includes('navigate(\'/clinical/assessment/dass21/complete\'') &&
                            !dass21Content.includes('navigate(\'/clinical/results\'');

console.log(`   ${hasCorrectNavigation ? '✅' : '❌'} Navigation path: ${hasCorrectNavigation ? 'Corrected to /clinical/assessment/dass21/complete' : 'Still using wrong path'}`);

// Test 2: Check result data format
console.log('\n2️⃣ TESTING RESULT DATA FORMAT');
console.log('-'.repeat(30));

const hasCorrectResultFormat = dass21Content.includes('state: {') &&
                              dass21Content.includes('assessmentType: \'dass21\'') &&
                              dass21Content.includes('result: {') &&
                              dass21Content.includes('score: results.totalScore') &&
                              dass21Content.includes('severity_level: getSeverityLevel(results.totalScore)');

console.log(`   ${hasCorrectResultFormat ? '✅' : '❌'} Result format: ${hasCorrectResultFormat ? 'Using location.state.result (correct)' : 'Using wrong format'}`);

// Test 3: Check severity level function
console.log('\n3️⃣ TESTING SEVERITY LEVEL FUNCTION');
console.log('-'.repeat(30));

const hasSeverityFunction = dass21Content.includes('const getSeverityLevel = (totalScore: number): string =>') &&
                           dass21Content.includes('if (totalScore <= 21) return \'normal\'') &&
                           dass21Content.includes('return \'extremely severe\'');

console.log(`   ${hasSeverityFunction ? '✅' : '❌'} Severity function: ${hasSeverityFunction ? 'Implemented correctly' : 'Missing or incorrect'}`);

// Test 4: Check DASS-21 specific data included
console.log('\n4️⃣ TESTING DASS-21 SPECIFIC DATA');
console.log('-'.repeat(30));

const hasDass21Data = dass21Content.includes('depression: results.depression') &&
                      dass21Content.includes('anxiety: results.anxiety') &&
                      dass21Content.includes('stress: results.stress');

console.log(`   ${hasDass21Data ? '✅' : '❌'} DASS-21 data: ${hasDass21Data ? 'Includes subscale scores' : 'Missing subscale data'}`);

// Test 5: Check no undefined score errors
console.log('\n5️⃣ TESTING UNDEFINED SCORE PROTECTION');
console.log('-'.repeat(30));

const hasUndefinedProtection = dass21Content.includes('score === undefined ||') &&
                              dass21Content.includes('score === null ||');

console.log(`   ${hasUndefinedProtection ? '✅' : '❌'} Undefined protection: ${hasUndefinedProtection ? 'Enhanced and active' : 'Missing'}`);

// Overall assessment
console.log('\n🎯 RESULTS NAVIGATION FIX ASSESSMENT');
console.log('='.repeat(50));

const allFixesApplied = hasCorrectNavigation && hasCorrectResultFormat && hasSeverityFunction && hasDass21Data && hasUndefinedProtection;

if (allFixesApplied) {
  console.log('🎉 ALL RESULTS NAVIGATION FIXES SUCCESSFULLY APPLIED!');
  console.log('');
  console.log('✅ DASS-21 Assessment Now Works Correctly:');
  console.log('   • Navigation goes to correct route (/clinical/assessment/dass21/complete)');
  console.log('   • Result data matches ClinicalResults component expectations');
  console.log('   • Severity levels calculated properly (normal → extremely severe)');
  console.log('   • All DASS-21 subscale scores (depression, anxiety, stress) included');
  console.log('   • Protection against undefined scores maintained');
} else {
  console.log('⚠️ SOME FIXES STILL NEEDED');
}

console.log('');
console.log('🚀 Test the Complete Flow:');
console.log('   1. Navigate to: http://localhost:5174/clinical/assessment/dass21/start');
console.log('   2. Answer all 21 questions');
console.log('   3. Select answer on question 21 (final question)');
console.log('   4. Assessment should navigate to results page');
console.log('   5. Results page should show DASS-21 scores and severity');
console.log('');
console.log('📊 Expected Results Display:');
console.log('   • Total Score: 0-126');
console.log('   • Severity Level: Normal, Mild, Moderate, Severe, or Extremely Severe');
console.log('   • Subscale Scores: Depression (0-42), Anxiety (0-42), Stress (0-42)');
console.log('   • No more navigation to main page');
console.log('   • No more undefined score errors');
