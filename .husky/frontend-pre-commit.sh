#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Move to frontend folder
cd frontend || exit 1

# Run frontend checks
npm run lint
npm run type-check
npm test
