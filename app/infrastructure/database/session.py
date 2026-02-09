"""Database session management and utilities.

Provides:
- Session factory configuration
- FastAPI dependency for database sessions
- Transaction context manager
- Proper session lifecycle management
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings


# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
    echo=settings.SQL_ECHO,  # Log SQL queries in debug mode
)

# Session factory
SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_session_factory() -> sessionmaker:
    """Get the configured session factory.
    
    Returns:
        Configured sessionmaker instance
    """
    return SessionFactory


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency to get database session.
    
    Provides a database session with automatic cleanup and error handling.
    Session commits on success, rolls back on error, and always closes.
    
    Yields:
        SQLAlchemy Session instance
        
    Example:
        ```python
        @app.get("/items/{item_id}")
        def get_item(item_id: int, db: Session = Depends(get_db_session)):
            return db.query(Item).filter(Item.id == item_id).first()
        ```
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()  # Commit if no exceptions
    except Exception:
        session.rollback()  # Rollback on any error
        raise
    finally:
        session.close()  # Always cleanup


@contextmanager
def transaction_context() -> Generator[Session, None, None]:
    """Context manager for explicit transaction control.
    
    Use this when you need manual control over transactions,
    such as in background tasks or batch operations.
    
    Yields:
        SQLAlchemy Session instance with transaction control
        
    Example:
        ```python
        from app.infrastructure.database.session import transaction_context
        
        def process_batch():
            with transaction_context() as session:
                # Do work with session
                item = session.query(Item).first()
                item.status = "processed"
                # Commits automatically on success
                # Rolls back on exception
        ```
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class SessionManager:
    """Advanced session manager for complex transaction scenarios.
    
    Provides more control over session lifecycle for cases where
    you need nested transactions or savepoints.
    
    Example:
        ```python
        async with SessionManager() as session:
            # Create savepoint
            with session.begin_nested():
                # Do risky operation
                ...
            # If we get here, savepoint succeeded
            # Main transaction commits on exit
        ```
    """
    
    def __init__(self):
        self.session: Session = None
    
    def __enter__(self) -> Session:
        """Enter the context and create session."""
        self.session = SessionFactory()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and cleanup session."""
        if exc_type is not None:
            # Exception occurred, rollback
            self.session.rollback()
        else:
            # Success, commit
            self.session.commit()
        
        # Always close
        self.session.close()
        
        # Don't suppress exceptions
        return False


def create_all_tables():
    """Create all database tables.
    
    Used for testing or initial setup. In production, use Alembic migrations.
    """
    from app.database import Base
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Drop all database tables.
    
    WARNING: Destructive operation. Use only in testing.
    """
    from app.database import Base
    Base.metadata.drop_all(bind=engine)
