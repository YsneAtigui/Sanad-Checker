"""Database infrastructure package.

Exports:
- get_db_session: FastAPI dependency for database sessions
- transaction_context: Context manager for explicit transactions
- SessionManager: Advanced session manager with savepoint support
"""

from app.infrastructure.database.session import (
    get_db_session,
    get_session_factory,
    transaction_context,
    SessionManager,
    create_all_tables,
    drop_all_tables,
)

__all__ = [
    "get_db_session",
    "get_session_factory",
    "transaction_context",
    "SessionManager",
    "create_all_tables",
    "drop_all_tables",
]
