from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env."""

    app_name: str = "AdventureWorks AI Platform API"
    environment: Literal["development", "staging", "production"] = "development"

    # SQL Server / Azure SQL connection
    sql_server: str = ""
    sql_database: str = ""
    sql_driver: str = "ODBC Driver 18 for SQL Server"
    # sql_auth_mode options:
    #   "windows"                    -> Trusted_Connection (local SQL Server / LocalDB)
    #   "sql"                        -> SQL login with sql_user/sql_password (avoid in Azure; dev only)
    #   "azure_ad_default"           -> Authentication=ActiveDirectoryDefault (local dev via az login/VS Code/Managed Identity)
    #   "azure_ad_interactive"       -> Authentication=ActiveDirectoryInteractive (browser login, local dev)
    #   "azure_ad_managed_identity"  -> Authentication=ActiveDirectoryManagedIdentity (Container Apps/App Service)
    sql_auth_mode: Literal[
        "windows", "sql", "azure_ad_default", "azure_ad_interactive", "azure_ad_managed_identity"
    ] = "windows"
    sql_user: str = ""
    sql_password: str = ""
    # Client ID of a user-assigned managed identity (leave blank for system-assigned)
    sql_managed_identity_client_id: str = ""
    # Entra tenant ID; forces token acquisition against the correct tenant instead of relying
    # on the browser's default/cached account, which can silently pick the wrong identity.
    azure_tenant_id: str = ""

    # Azure AI Foundry / Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-10-21"
    # Managed identity client ID for token acquisition (leave blank for system-assigned/local dev credential chain)
    azure_openai_managed_identity_client_id: str = ""

    # Azure Storage (blob-based exports/artifacts)
    azure_storage_account_url: str = ""
    azure_storage_container: str = "forecast-exports"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for dependency injection."""
    return Settings()
