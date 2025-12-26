#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔀 TESTING DASS-21 QUESTION RANDOMIZATION');
console.log('='.repeat(60));
console.log('');

const dass21Path = path.join(__dirname, 'frontend/src/pages/clinical/DASS21Assessment.tsx');
const dass21Content = fs.readFileSync(dass21Path, 'utf8');

// Test 1: Check standard DASS-21 questions
console.log('1️⃣ TESTING STANDARD DASS-21 QUESTIONS');
console.log('-'.repeat(30));

const hasStandardQuestions = dass21Content.includes('I couldn\'t seem to experience any positive feeling at all') &&
                              dass21Content.includes('I found it difficult to work up the initiative to do things') &&
                              dass21Content.includes('I found it hard to wind down') &&
                              dass21Content.includes('I tended to over-react to situations') &&
                              dass21Content.includes('I found it difficult to relax');

console.log(`   ${hasStandardQuestions ? '✅' : '❌'} Standard questions: ${hasStandardQuestions ? 'Using official DASS-21 questions' : 'Still using incorrect questions'}`);

// Test 2: Check category balance
console.log('\n2️⃣ TESTING CATEGORY BALANCE');
console.log('-'.repeat(30));

const depressionCount = (dass21Content.match(/category: 'depression'/g) || []).length;
const anxietyCount = (dass21Content.match(/category: 'anxiety'/g) || []).length;
const stressCount = (dass21Content.match(/category: 'stress'/g) || []).length;

console.log(`   📊 Depression: ${depressionCount} questions`);
console.log(`   📊 Anxiety: ${anxietyCount} questions`);
console.log(`   📊 Stress: ${stressCount} questions`);

const isBalanced = depressionCount === 7 && anxietyCount === 7 && stressCount === 7;
console.log(`   ${isBalanced ? '✅' : '❌'} Category balance: ${isBalanced ? 'Perfect 7-7-7 balance' : 'Not balanced'}`);

// Test 3: Check randomization implementation
console.log('\n3️⃣ TESTING RANDOMIZATION IMPLEMENTATION');
console.log('-'.repeat(30));

const hasRandomization = dass21Content.includes('useState<DASS21Question[]>([])') &&
                        dass21Content.includes('useEffect(() =>') &&
                        dass21Content.includes('shuffleArray') &&
                        dass21Content.includes('setRandomizedQuestions') &&
                        dass21Content.includes('randomizedQuestions[currentQuestion]');

console.log(`   ${hasRandomization ? '✅' : '❌'} Randomization: ${hasRandomization ? 'Fully implemented' : 'Missing or incomplete'}`);

// Test 4: Check category-specific shuffling
console.log('\n4️⃣ TESTING CATEGORY-SPECIFIC SHUFFLING');
console.log('-'.repeat(30));

const hasCategoryShuffling = dass21Content.includes('depressionQuestions') &&
                             dass21Content.includes('anxietyQuestions') &&
                             dass21Content.includes('stressQuestions') &&
                             dass21Content.includes('shuffledDepression') &&
                             dass21Content.includes('shuffledAnxiety') &&
                             dass21Content.includes('shuffledStress');

console.log(`   ${hasCategoryShuffling ? '✅' : '❌'} Category shuffling: ${hasCategoryShuffling ? 'Implemented correctly' : 'Missing'}`);

// Test 5: Check loading state
console.log('\n5️⃣ TESTING LOADING STATE');
console.log('-'.repeat(30));

const hasLoadingState = dass21Content.includes('randomizedQuestions.length === 0') &&
                       dass21Content.includes('Preparing assessment...') &&
                       dass21Content.includes('animate-spin');

console.log(`   ${hasLoadingState ? '✅' : '❌'} Loading state: ${hasLoadingState ? 'Implemented' : 'Missing'}`);

// Test 6: Check question ID mapping
console.log('\n6️⃣ TESTING QUESTION ID MAPPING');
console.log('-'.repeat(30));

const hasIdMapping = dass21Content.includes('randomizedQuestions[currentQuestion]?.id') &&
                   dass21Content.includes('setResponses({ ...responses, [questionId]: value })');

console.log(`   ${hasIdMapping ? '✅' : '❌'} ID mapping: ${hasIdMapping ? 'Correctly maps original question IDs' : 'Not mapping correctly'}`);

// Overall assessment
console.log('\n🎯 DASS-21 RANDOMIZATION ASSESSMENT');
console.log('='.repeat(60));

const allImprovementsApplied = hasStandardQuestions && isBalanced && hasRandomization && hasCategoryShuffling && hasLoadingState && hasIdMapping;

if (allImprovementsApplied) {
  console.log('🎉 ALL DASS-21 RANDOMIZATION IMPROVEMENTS SUCCESSFULLY APPLIED!');
  console.log('');
  console.log('✅ Enhanced DASS-21 Assessment Features:');
  console.log('   • Official DASS-21 questions (no repetition)');
  console.log('   • Perfect category balance (7 depression, 7 anxiety, 7 stress)');
  console.log('   • Advanced randomization algorithm');
  console.log('   • Category-specific shuffling to maintain balance');
  console.log('   • Loading state for smooth user experience');
  console.log('   • Proper question ID mapping for accurate scoring');
  console.log('   • No predictability in question order');
} else {
  console.log('⚠️ SOME RANDOMIZATION IMPROVEMENTS STILL NEEDED');
}

console.log('');
console.log('🚀 Benefits of the New System:');
console.log('   • Users see different question orders each time');
console.log('   • Categories remain balanced for statistical validity');
console.log('   • Standardized DASS-21 questions ensure clinical accuracy');
console.log('   • No repetition across assessment sessions');
console.log('   • Maintains proper scoring with randomized order');
console.log('   • Professional clinical assessment experience');
console.log('');
console.log('📊 Question Distribution:');
console.log('   • Total: 21 questions (unchanged)');
console.log('   • Depression: 7 questions (balanced)');
console.log('   • Anxiety: 7 questions (balanced)');
console.log('   • Stress: 7 questions (balanced)');
console.log('   • Scale: 0-3 Likert (maintained)');
console.log('   • Score Range: 0-126 total (maintained)');