#!/usr/bin/env sh
# Build the frontend with API base URL pointing at the deployed backend.
# Usage:
#   ./scripts/build-with-api-base.sh
#   VITE_API_BASE=https://your-app.run.app npm run build
#
# Or set once:
#   export VITE_API_BASE=https://xxxxx.us-east-1.awsapprunner.com
#   npm run build
#
# Windows (PowerShell): $env:VITE_API_BASE="https://xxxxx.us-east-1.awsapprunner.com"; npm run build
# Windows (cmd): set VITE_API_BASE=https://xxxxx.us-east-1.awsapprunner.com && npm run build

if [ -z "$VITE_API_BASE" ]; then
  echo "VITE_API_BASE is not set. Set it to your backend URL (e.g. https://your-app.run.app)."
  echo "Example: VITE_API_BASE=https://xxxxx.us-east-1.awsapprunner.com ./scripts/build-with-api-base.sh"
  exit 1
fi

npm run build
