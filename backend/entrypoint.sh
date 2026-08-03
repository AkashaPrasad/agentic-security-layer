#!/bin/sh
# ==============================================================================
# Backend entrypoint — waits for Postgres, runs migrations, starts server
# ==============================================================================

set -e

echo "⏳  Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until python -c "
import asyncio, asyncpg, os, sys
async def check():
    try:
        conn = await asyncpg.connect(
            host=os.environ['POSTGRES_HOST'],
            port=int(os.environ.get('POSTGRES_PORT', 5432)),
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            database=os.environ['POSTGRES_DB'],
        )
        await conn.close()
    except Exception as e:
        sys.exit(1)
asyncio.run(check())
" 2>/dev/null; do
    sleep 1
done
echo "✅  PostgreSQL is ready."

echo "⏳  Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
until python -c "
import redis, os, sys
try:
    r = redis.Redis(host=os.environ['REDIS_HOST'], port=int(os.environ.get('REDIS_PORT', 6379)))
    r.ping()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "✅  Redis is ready."

echo "⚠️  Skipping database migrations (disabled temporarily)."
# echo "🔄  Running database migrations..."
# alembic upgrade head
# echo "✅  Migrations complete."

echo "🚀  Starting $1..."
exec "$@"
