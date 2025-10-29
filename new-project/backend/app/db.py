import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

import socket

# Build DATABASE_URL from env components when DATABASE_URL not provided.
# Default DB host for Docker Compose is the service name `db`.
DB_HOST = os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'db'))
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'postgres')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def wait_for_db(url: str, timeout: int = 30, interval: float = 1.0) -> None:
    """Try connecting to the DB until timeout (seconds). Raises last exception on failure.

    This helps when Postgres container takes a few seconds to become ready.
    """
    engine = create_engine(url)
    start = time.time()
    last_exc = None
    while True:
        try:
            with engine.connect():
                logging.info('Database reachable')
                return
        except OperationalError as e:
            last_exc = e
            # Detect DNS/hostname resolution issues and give actionable guidance
            msg = str(e)
            if 'could not translate host name' in msg or 'Name or service not known' in msg:
                # Try a quick local resolution check
                try:
                    socket.gethostbyname(DB_HOST)
                except Exception:
                    logging.error("Hostname '%s' could not be resolved. If running in Docker, ensure the Postgres service name in docker-compose is '%s' or set DATABASE_URL to a reachable host.", DB_HOST, DB_HOST)
                    logging.error("Original error: %s", msg)
                    raise
            elapsed = time.time() - start
            if elapsed >= timeout:
                logging.error('Timed out waiting for database')
                # raise the original exception to preserve details
                raise last_exc
            logging.info('Waiting for database to be ready... sleeping %.1fs', interval)
            time.sleep(interval)


# Wait a short time for the DB when running in containerized environments
try:
    wait_for_db(DATABASE_URL, timeout=30, interval=1.0)
except Exception:
    # Let the normal SQLAlchemy errors surface later; we log and continue so the app can start (optional)
    logging.exception('Database did not become ready in time')


# Using SQLAlchemy (synchronous) engine with psycopg2
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency that provides a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
