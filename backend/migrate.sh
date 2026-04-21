#!/bin/bash
set -e

echo "=========================================="
echo "🚀 Starting Database Migrations"
echo "=========================================="
echo "Time: $(date)"
echo "Database URL: ${DATABASE_URL:0:50}..."
echo ""

# Run migrations with verbose output
echo "📝 Running: alembic upgrade head"
alembic upgrade head || {
    echo "❌ Migrations FAILED!"
    exit 1
}

echo ""
echo "✅ Migrations COMPLETED successfully!"
echo "=========================================="
echo ""

# Start the application
echo "🚀 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
