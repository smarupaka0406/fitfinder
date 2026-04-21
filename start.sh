#!/usr/bin/env bash
set -e
cd backend
gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 2
