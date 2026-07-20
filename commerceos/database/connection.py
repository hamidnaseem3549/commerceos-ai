"""Database connection management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from commerceos.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionFactory = sessionmaker(bind=engine)


def init_db():
    from commerceos.database.models import Base
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a fresh database session. Caller must close()."""
    return SessionFactory()
