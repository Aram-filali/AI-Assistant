"""
Initialize database tables by creating them directly with SQLAlchemy.
This bypasses Alembic and ensures tables exist before the app starts.
"""
import logging
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)

def init_database():
    """
    Create all database tables if they don't exist.
    Uses the sync DATABASE_URL to create tables.
    """
    print("=" * 60)
    print("🚀 Starting Database Initialization")
    print("=" * 60)
    print()
    
    try:
        # Get sync database URL
        db_url = settings.DATABASE_URL_SYNC or settings.DATABASE_URL.replace("+asyncpg", "")
        
        print(f"📝 Connecting to database: {db_url[:60]}...")
        
        # Create synchronous engine
        engine = create_engine(
            db_url,
            echo=True,  # Print SQL statements
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create the "app" schema if it doesn't exist
        with engine.connect() as conn:
            print("📋 Creating 'app' schema if it doesn't exist...")
            conn.execute(text('CREATE SCHEMA IF NOT EXISTS app'))
            conn.commit()
            print("   ✓ Schema ready")
        
        # Check which tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names(schema="app")
        
        print(f"   Found {len(existing_tables)} existing tables in 'app' schema: {existing_tables}")
        print()
        
        # Create all tables from models
        print("📋 Creating missing tables...")
        Base.metadata.create_all(engine)
        
        # Check again after creation
        inspector = inspect(engine)
        final_tables = inspector.get_table_names(schema="app")
        
        print()
        print(f"✅ Database now has {len(final_tables)} tables in 'app' schema: {final_tables}")
        print()
        print("=" * 60)
        print("✅ Database Initialization COMPLETED successfully!")
        print("=" * 60)
        print()
        
        # Close the engine
        engine.dispose()
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Database Initialization FAILED!")
        print(f"Error: {str(e)}")
        print("=" * 60)
        print()
        
        # Log the full error
        logger.exception("Database initialization failed")
        raise

if __name__ == "__main__":
    init_database()
