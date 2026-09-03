#!/usr/bin/env node

/**
 * Script to automatically add React.memo to components
 *
 * Usage: node scripts/add-memo.js <component-file>
 */

const fs = require('fs');
const path = require('path');

const COMPONENTS_TO_MEMOIZE = [
  'frontend/src/components/ui/Select.tsx',
  'frontend/src/components/ui/Textarea.tsx',
  'frontend/src/components/ui/Input.tsx',
  'frontend/src/components/ui/Alert.tsx',
  'frontend/src/components/ui/progress.tsx',
  'frontend/src/components/ui/button.tsx',
  'frontend/src/components/ui/checkbox.tsx',
  'frontend/src/components/ui/radio-group.tsx',
  'frontend/src/components/ui/tabs.tsx',
  'frontend/src/components/ui/table.tsx',
  'frontend/src/components/ui/separator.tsx',
  'frontend/src/components/ui/dialog.tsx',
];

function addReactMemoToFile(filePath) {
  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  File not found: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf-8');

  // Skip if already has React.memo
  if (content.includes('React.memo')) {
    console.log(`✓ Already has React.memo: ${filePath}`);
    return false;
  }

  // Pattern 1: export const ComponentName: React.FC<PropsType> = ({ =>
  const pattern1 = /export const (\w+):\s*React\.FC<([^>]+)>\s*=\s*\((\{[^)]*\})\)\s*=>\s*\{/g;

  // Pattern 2: const ComponentName: React.FC<PropsType> = ({ =>
  const pattern2 = /const (\w+):\s*React\.FC<([^>]+)>\s*=\s*\((\{[^)]*\})\)\s*=>\s*\{/g;

  let modified = false;
  let componentName = '';

  // Try pattern 1
  content = content.replace(pattern1, (match, name, props, params) => {
    componentName = name;
    modified = true;
    return `export const ${name} = React.memo<${props}>(${params} => {`;
  });

  // If pattern 1 didn't match, try pattern 2
  if (!modified) {
    content = content.replace(pattern2, (match, name, props, params) => {
      componentName = name;
      modified = true;
      return `const ${name} = React.memo<${props}>(${params} => {`;
    });
  }

  if (modified) {
    // Add displayName after the component closing
    const closingPattern = new RegExp(`(export const ${componentName}|const ${componentName}).*?^};\\s*$`, 'gm');
    const lastClosingBracket = content.lastIndexOf('};');

    if (lastClosingBracket !== -1) {
      const insertPosition = content.indexOf('}', lastClosingBracket);
      const indent = 'export const ' === content.substring(insertPosition - 13, insertPosition) ? '' : '  ';

      content = content.substring(0, insertPosition + 1) +
        `\n\n${componentName}.displayName = '${componentName}';` +
        content.substring(insertPosition + 1);

      fs.writeFileSync(filePath, content, 'utf-8');
      console.log(`✅ Added React.memo to ${componentName} in ${path.basename(filePath)}`);
      return true;
    }
  }

  if (!modified) {
    console.log(`⚠️  Could not find suitable component pattern in ${filePath}`);
  }

  return modified;
}

// Process all components
let successCount = 0;
let skipCount = 0;

console.log('🚀 Adding React.memo to components...\n');

COMPONENTS_TO_MEMOIZE.forEach(filePath => {
  if (addReactMemoToFile(filePath)) {
    successCount++;
  } else {
    skipCount++;
  }
});

console.log(`\n✨ Complete!`);
console.log(`   ✅ Modified: ${successCount} files`);
console.log(`   ⏭️  Skipped: ${skipCount} files`);
