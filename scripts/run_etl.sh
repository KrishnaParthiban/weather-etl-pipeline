#!/usr/bin/env bash
# Runs the pipeline once. Cron calls this file every hour.
cd "$(dirname "$0")/.." || exit 1
source venv/bin/activate
python main.py >> logs/cron.log 2>&1
