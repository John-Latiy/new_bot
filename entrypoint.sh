#!/usr/bin/env bash
set -euo pipefail

# Prepare runtime dirs
mkdir -p /app/data /app/logs /app/data/covers /app/sessions

# Initialize SQLite tables if needed
python /app/create_db.py || true

exec "$@"
