#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z klepp-postgres-db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

uvicorn main:app --reload --workers 1 --host 0.0.0.0 --port 8004
