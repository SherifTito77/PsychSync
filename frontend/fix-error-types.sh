#!/bin/bash

# Script to fix 'err: any' types across all TypeScript/TSX files
# This replaces unsafe 'any' error types with proper error handling

echo "Starting error type fixes..."
echo "=============================="

# Find all TypeScript files
files=$(find src -name "*.tsx" -o -name "*.ts")

count=0
for file in $files; do
  # Check if file contains "} catch (err: any) {"
  if grep -q "} catch (err: any)" "$file"; then
    # Replace "} catch (err: any) {" with "} catch (err) {"
    sed -i '' 's/} catch (err: any) {/} catch (err) {/g' "$file"
    count=$((count + 1))
    echo "✓ Fixed: $file"
  fi
done

echo ""
echo "=============================="
echo "Fixed $count files!"
echo "Error type fixing complete!"
