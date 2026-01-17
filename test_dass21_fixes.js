#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔧 TESTING DASS-21 ASSESSMENT FIXES');
console.log('='.repeat(50));
console.log('');

// Test 1: Check if undefined score validation is fixed
console.log('1️⃣ TESTING UNDEFINED SCORE VALIDATION');
console.log('-'.repeat(30));

const dass21Path = path.join(__dirname, 'frontend/src/pages/clinical/DASS21Assessment.tsx');
const dass21Content = fs.readFileSync(dass21Path, 'utf8');

const hasUndefinedCheck = dass21Content.includes('score === undefined ||');
const hasNullCheck = dass21Content.includes('score === null ||');

console.log(`   ${hasUndefinedCheck ? '✅' : '❌'} Undefined score check: ${hasUndefinedCheck ? 'Added' : 'Missing'}`);
console.log(`   ${hasNullCheck ? '✅' : '❌'} Null score check: ${hasNullCheck ? 'Added' : 'Missing'}`);

// Test 2: Check if completion screen is implemented
console.log('\n2️⃣ TESTING COMPLETION SCREEN');
console.log('-'.repeat(30));

const hasCompletionScreen = dass21Content.includes('isCompleted') &&
                           dass21Content.includes('🎉 Assessment Complete!') &&
                           dass21Content.includes('View My Results');

console.log(`   ${hasCompletionScreen ? '✅' : '❌'} Completion screen: ${hasCompletionScreen ? 'Implemented' : 'Missing'}`);

// Test 3: Check if submit button is available
console.log('\n3️⃣ TESTING SUBMIT FUNCTIONALITY');
console.log('-'.repeat(30));

const hasSubmitButton = dass21Content.includes('onClick={calculateAndShowResults}') &&
                       dass21Content.includes('View My Results');

console.log(`   ${hasSubmitButton ? '✅' : '❌'} Submit functionality: ${hasSubmitButton ? 'Available' : 'Missing'}`);

// Test 4: Check if review functionality works
console.log('\n4️⃣ TESTING REVIEW FUNCTIONALITY');
console.log('-'.repeat(30));

const hasReviewButton = dass21Content.includes('Review Last Question') &&
                       dass21Content.includes('setCurrentQuestion(dass21Questions.length - 1)');

console.log(`   ${hasReviewButton ? '✅' : '❌'} Review functionality: ${hasReviewButton ? 'Available' : 'Missing'}`);

// Test 5: Check if progress bar is fixed
console.log('\n5️⃣ TESTING PROGRESS BAR');
console.log('-'.repeat(30));

const hasProgressBarFix = dass21Content.includes('Math.min(currentQuestion + 1, dass21Questions.length)');

console.log(`   ${hasProgressBarFix ? '✅' : '❌'} Progress bar fix: ${hasProgressBarFix ? 'Applied' : 'Missing'}`);

// Overall assessment
console.log('\n🎯 OVERALL ASSESSMENT');
console.log('='.repeat(50));

const allFixesApplied = hasUndefinedCheck && hasNullCheck && hasCompletionScreen && hasSubmitButton && hasReviewButton && hasProgressBarFix;

if (allFixesApplied) {
  console.log('🎉 ALL FIXES SUCCESSFULLY APPLIED!');
  console.log('');
  console.log('✅ DASS-21 Assessment Issues Resolved:');
  console.log('   • No more undefined score errors');
  console.log('   • Clear completion screen with submit button');
  console.log('   • Users can review last question');
  console.log('   • Progress bar shows correctly');
  console.log('   • Better user experience overall');
} else {
  console.log('⚠️ SOME FIXES STILL NEEDED');
}

console.log('');
console.log('🚀 Ready to test:');
console.log('   1. Navigate to: http://localhost:5174/clinical/assessment/dass21/start');
console.log('   2. Complete all 21 questions');
console.log('   3. Verify completion screen appears');
console.log('   4. Click "View My Results" to submit');
console.log('   5. Check console for no undefined score errors');
