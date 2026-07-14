import logging
import struct
from collections.abc import Generator
from functools import lru_cache
from typing import Any

import pyodbc
from sqlalchemy import create_engine, pool, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ODBC connection attribute used to hand pyodbc a pre-acquired Entra ID access token,
# bypassing the ODBC driver's own embedded browser/WAM broker (which some EDR tools,
# e.g. CrowdStrike Falcon, terminate as suspicious child-process/webview activity).
SQL_COPT_SS_ACCESS_TOKEN = 1256
_AAD_TOKEN_SCOPE = "https://database.windows.net/.default"
_TOKEN_AUTH_MODES = {"azure_ad_default", "azure_ad_interactive"}


class Base(DeclarativeBase):
    """Base model class for ORM entities."""


def build_connection_string() -> str:
    """Build the pyodbc connection string for SQL Server / Azure SQL.

    Auth mode is controlled by SQL_AUTH_MODE:
      - windows                   -> Trusted_Connection (local SQL Server / LocalDB)
      - sql                       -> SQL login with SQL_USER/SQL_PASSWORD (dev only, avoid in Azure)
      - azure_ad_default          -> Entra ID token acquired via azure-identity DefaultAzureCredential
      - azure_ad_interactive      -> Entra ID token acquired via azure-identity InteractiveBrowserCredential
      - azure_ad_managed_identity -> Authentication=ActiveDirectoryManagedIdentity (Container Apps/App Service)

    For azure_ad_default/azure_ad_interactive the token is supplied separately via the
    SQL_COPT_SS_ACCESS_TOKEN connection attribute (see get_pyodbc_connection), so no
    "Authentication=" keyword is included in the string for those modes.
    """
    settings = get_settings()
    if not settings.sql_server or not settings.sql_database:
        raise ValueError("SQL_SERVER and SQL_DATABASE must be configured in environment")

    driver = settings.sql_driver or "ODBC Driver 18 for SQL Server"
    server_name = settings.sql_server.replace("\\\\", "\\")
    is_azure_sql = ".database.windows.net" in server_name.lower()

    base = f"Driver={{{driver}}};Server={server_name};Database={settings.sql_database};"
    # Azure SQL requires encrypted connections with a trusted cert; local SQL Server/LocalDB
    # typically presents a self-signed cert, so trust it to allow the local connection.
    tls = "Encrypt=yes;TrustServerCertificate=no;" if is_azure_sql else "Encrypt=no;TrustServerCertificate=yes;"

    auth_mode = settings.sql_auth_mode
    if auth_mode == "windows":
        connection_string = f"{base}Trusted_Connection=yes;{tls}Connection Timeout=30;"
    elif auth_mode == "sql":
        if not (settings.sql_user and settings.sql_password):
            raise ValueError("SQL_USER and SQL_PASSWORD must be set when SQL_AUTH_MODE=sql")
        connection_string = f"{base}UID={settings.sql_user};PWD={settings.sql_password};{tls}Connection Timeout=30;"
    elif auth_mode in _TOKEN_AUTH_MODES:
        # No Authentication/UID keyword here; the token is supplied via attrs_before instead.
        connection_string = f"{base}{tls}Connection Timeout=30;"
    elif auth_mode == "azure_ad_managed_identity":
        client_id = settings.sql_managed_identity_client_id
        uid_clause = f"UID={client_id};" if client_id else ""
        connection_string = f"{base}{uid_clause}Authentication=ActiveDirectoryManagedIdentity;{tls}Connection Timeout=30;"
    else:
        raise ValueError(f"Unsupported SQL_AUTH_MODE: {auth_mode}")

    logger.info(f"Database connection configured for server: {server_name} (auth_mode={auth_mode})")
    return connection_string


def build_connection_args() -> dict[str, str]:
    """Build the pyodbc connection arguments for SQL Server."""
    return {"odbc_connect": build_connection_string()}


@lru_cache
def _get_token_credential(auth_mode: str, managed_identity_client_id: str = ""):
    """Return a cached azure-identity credential for the given token-based auth mode.

    Caching is important: credentials cache their acquired tokens internally, so reusing
    the same instance across pooled connections avoids re-prompting for login on every
    new SQLAlchemy connection.
    """
    from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential

    settings = get_settings()
    if auth_mode == "azure_ad_interactive":
        # Uses the system default browser (a real OS process), not the ODBC driver's
        # embedded WebView/WAM broker, so it isn't caught by EDR tools blocking the latter.
        # tenant_id/login_hint force the correct Entra account/tenant instead of relying on
        # whatever session the browser has cached, which otherwise causes SQL Server to
        # reject the token with "Login failed for user '<token-identified principal>'".
        kwargs: dict[str, str] = {}
        if settings.azure_tenant_id:
            kwargs["tenant_id"] = settings.azure_tenant_id
        if settings.sql_user:
            kwargs["login_hint"] = settings.sql_user
        return InteractiveBrowserCredential(**kwargs)
    if auth_mode == "azure_ad_default":
        return DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id or None)
    raise ValueError(f"No token credential available for auth_mode={auth_mode}")


def _build_access_token_attr() -> bytes:
    """Acquire an Entra ID access token and pack it into the SQL_COPT_SS_ACCESS_TOKEN struct."""
    settings = get_settings()
    credential = _get_token_credential(settings.sql_auth_mode, settings.sql_managed_identity_client_id)
    token = credential.get_token(_AAD_TOKEN_SCOPE).token
    token_bytes = token.encode("utf-16-le")
    return struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)


def get_pyodbc_connection() -> pyodbc.Connection:
    """Return a direct pyodbc connection using the configured SQL Server settings."""
    settings = get_settings()
    connection_string = build_connection_string()
    if settings.sql_auth_mode in _TOKEN_AUTH_MODES:
        return pyodbc.connect(
            connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: _build_access_token_attr()}
        )
    return pyodbc.connect(connection_string)



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
