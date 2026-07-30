from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def is_database_ready(session: Session) -> bool:
    """Return whether PostgreSQL answers the smallest useful query."""
    try:
        return bool(session.scalar(text("SELECT 1")) == 1)
    except SQLAlchemyError:
        return False
