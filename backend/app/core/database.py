import logging
from collections.abc import Generator
from typing import Any

import pyodbc
from sqlalchemy import create_engine, pool, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base model class for ORM entities."""


def build_connection_string() -> str:
    """Build the pyodbc connection string for SQL Server."""
    settings = get_settings()
    if not settings.sql_server or not settings.sql_database:
        raise ValueError("SQL_SERVER and SQL_DATABASE must be configured in environment")

    driver = settings.sql_driver or "ODBC Driver 18 for SQL Server"
    server_name = settings.sql_server.replace("\\\\", "\\")

    if settings.sql_trusted_connection or not (settings.sql_user and settings.sql_password):
        connection_string = (
            f"Driver={{{driver}}};"
            f"Server={server_name};"
            f"Database={settings.sql_database};"
            "Trusted_Connection=yes;"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )
    else:
        connection_string = (
            f"Driver={{{driver}}};"
            f"Server={server_name};"
            f"Database={settings.sql_database};"
            f"UID={settings.sql_user};"
            f"PWD={settings.sql_password};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )

    logger.info(f"Database connection configured for server: {server_name}")
    return connection_string


def build_connection_args() -> dict[str, str]:
    """Build the pyodbc connection arguments for SQL Server."""
    return {"odbc_connect": build_connection_string()}


def get_pyodbc_connection() -> pyodbc.Connection:
    """Return a direct pyodbc connection using the configured SQL Server settings."""
    return pyodbc.connect(build_connection_string())


try:
    engine = create_engine(
        "mssql+pyodbc://",
        creator=get_pyodbc_connection,
        poolclass=pool.QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
    )
    logger.info("SQLAlchemy engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, Any, None]:
    """Provide a database session for request handling with error handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_connection() -> bool:
    """Verify database connectivity."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection verified")
            return True
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False
