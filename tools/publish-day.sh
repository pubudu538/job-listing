#!/bin/bash
# Builds the daily pages from data/*.json, commits and pushes to GitHub Pages.
# Used by the "Daily BA / PM job watch" scheduled task. Takes no arguments.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
/usr/bin/python3 -I tools/build.py
git add data daily
if git diff --cached --quiet; then
  echo "nothing new to commit"
else
  git commit -q -m "Daily job watch $(date +%Y-%m-%d)"
  echo "committed"
fi
git push -q origin HEAD:main
echo "pushed"
echo "page: https://pubudu538.github.io/job-listing/daily/$(date +%Y-%m-%d).html"
