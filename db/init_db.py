"""
Database initialization script.
Creates all database tables in SQLite or PostgreSQL.
"""

from db.database import engine, Base
# Import models to register them
from db.models import QueryLog, Recommendation, Collaboration, ProjectSuggestion, Feedback
from core.logger import logger

def init_database():
    """Create all relational database tables."""
    logger.info("Initializing database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_database()
