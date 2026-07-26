"""Database connection management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from commerceos.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionFactory = sessionmaker(bind=engine)


def init_db():
    """Create all database tables from the ORM models.

    Idempotent — safe to call multiple times. Tables that already
    exist are not recreated.
    """


def get_session():
    """Get a fresh database session. Caller must close()."""
    return SessionFactory()
