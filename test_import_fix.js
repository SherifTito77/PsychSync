#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔍 Testing Clinical Assessment Import Fix...\n');

// Check if all required files exist
const basePath = '/Users/sheriftito/Downloads/psychsync/frontend/src';
const requiredFiles = [
  'pages/ClinicalConsent.tsx',
  'pages/clinical/AssessmentRouter.tsx',
  'pages/clinical/DASS21Assessment.tsx',
  'pages/clinical/PCL5Assessment.tsx',
  'pages/clinical/AUDITAssessment.tsx'
];

let allFilesExist = true;

console.log('📁 Checking file existence:');
requiredFiles.forEach(file => {
  const filePath = path.join(basePath, file);
  const exists = fs.existsSync(filePath);
  console.log(`   ${exists ? '✅' : '❌'} ${file}`);
  if (!exists) allFilesExist = false;
});

// Check the import statement in AssessmentRouter
const routerPath = path.join(basePath, 'pages/clinical/AssessmentRouter.tsx');
const routerContent = fs.readFileSync(routerPath, 'utf8');

console.log('\n🔍 Analyzing AssessmentRouter imports:');

const hasDass21 = routerContent.includes("import DASS21Assessment from './DASS21Assessment'");
const hasPcl5 = routerContent.includes("import PCL5Assessment from './PCL5Assessment'");
const hasAudit = routerContent.includes("import AUDITAssessment from './AUDITAssessment'");
const hasConsentCorrect = routerContent.includes("import ClinicalConsent from '../ClinicalConsent'");
const hasConsentWrong = routerContent.includes("import ClinicalConsent from './ClinicalConsent'");

console.log(`   ✅ DASS21 import: ${hasDass21 ? 'Correct' : 'Missing'}`);
console.log(`   ✅ PCL5 import: ${hasPcl5 ? 'Correct' : 'Missing'}`);
console.log(`   ✅ AUDIT import: ${hasAudit ? 'Correct' : 'Missing'}`);
console.log(`   ${hasConsentCorrect ? '✅' : '❌'} ClinicalConsent import: ${hasConsentCorrect ? 'Correct (../ClinicalConsent)' : hasConsentWrong ? 'Wrong (./ClinicalConsent)' : 'Missing'}`);

// Check if ClinicalConsent exports a default component
const consentPath = path.join(basePath, 'pages/ClinicalConsent.tsx');
const consentContent = fs.readFileSync(consentPath, 'utf8');

const hasDefaultExport = consentContent.includes('export default');
const hasReactComponent = consentContent.includes('React.FC') || consentContent.includes('React.Component');

console.log('\n📄 Analyzing ClinicalConsent component:');
console.log(`   ${hasDefaultExport ? '✅' : '❌'} Default export: ${hasDefaultExport ? 'Yes' : 'No'}`);
console.log(`   ${hasReactComponent ? '✅' : '❌'} React component: ${hasReactComponent ? 'Yes' : 'No'}`);

// Overall assessment
console.log('\n🎯 Overall Assessment:');
if (allFilesExist && hasConsentCorrect && hasDefaultExport && hasReactComponent) {
  console.log('   ✅ All imports should work correctly');
  console.log('   🔧 The import error should be resolved');
} else {
  console.log('   ❌ There are still some issues to fix:');

  if (!allFilesExist) console.log('      • Some required files are missing');
  if (!hasConsentCorrect) console.log('      • ClinicalConsent import path is incorrect');
  if (!hasDefaultExport) console.log('      • ClinicalConsent does not export a default component');
  if (!hasReactComponent) console.log('      • ClinicalConsent is not a valid React component');
}

console.log('\n💡 To test the fix:');
console.log('   1. Try accessing: http://localhost:5176/clinical/assessment/dass21/start');
console.log('   2. Clear browser cache and refresh');
console.log('   3. Check browser console for any remaining errors');