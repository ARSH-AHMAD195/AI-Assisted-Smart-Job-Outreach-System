from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
import logging

try:
    from config import settings
except ImportError:
    from app.config import settings


# ----------- LOGGER & BASE INITIALIZATION -----------

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# ----------- ENGINE -----------

engine = create_engine(
    settings.get_settings().DATABASE_URL,
    echo=settings.get_settings().DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ----------- SESSION LOCAL -----------

session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# ----------- DATABASE SESSION FUNCTIONS -----------

def get_db():
    db: Session = session_local()
    try:
        yield db
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Database error: {exc}")
        raise
    finally:
        db.close()

def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as exc:
        logger.error(f"Database connection failed: {exc}")
        return False

def close_db_connection():
    try:
        engine.dispose()
        logger.info("Database connection closed")
    except Exception as exc:
        logger.error(f"Database connection close failed: {exc}", exc_info=True)
        raise