#!/bin/sh
# Wait for PostgreSQL to be ready

echo "Waiting for PostgreSQL..."

for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
  if python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; then
    echo "✓ PostgreSQL is ready!"
    exit 0
  fi
  echo "Attempt $i/30: PostgreSQL not ready, waiting..."
  sleep 2
done

echo "✗ Timeout waiting for PostgreSQL"
exit 1
