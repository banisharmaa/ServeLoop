"""
database/db.py

Thin DB wrapper to centralize session/engine access for ServeLoop.

Provides:
- init_db(): create tables (calls models.init_db)
- get_session(): return a new session (SQLAlchemy session)
- db_session: a convenience long-lived session (use carefully in dev)
- engine, SessionLocal (re-exported)

Note: For Streamlit quick demos a single shared session (db_session) can be convenient.
In production prefer short-lived sessions via get_session() and proper scoping.
"""
from database.models import engine, SessionLocal, init_db as _init_db, get_session as _get_session

# Re-export useful items
engine = engine
SessionLocal = SessionLocal


def init_db():
    """Initialize DB schema (tables)."""
    _init_db()


def get_session():
    """Return a new SQLAlchemy session. Caller should close it."""
    return _get_session()

# Convenience single session for quick Streamlit use (autoclose not handled)
# Use with caution; better to use get_session() per request for safety.
try:
    db_session = SessionLocal()
except Exception:
    db_session = None


# Quick self-test
if __name__ == "__main__":
    print("Initializing DB...")
    init_db()
    s = get_session()
    print("Session obtained:", s)
    s.close()
