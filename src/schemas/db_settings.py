from os import environ

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

load_dotenv(".env")


class DBSettings(BaseSettings):
    DUCKDB_PATH: str = Field(
        ..., title="DuckDB Path", description="Path to DuckDB database"
    )
    PINECONE_API_KEY: SecretStr = Field(
        ..., title="Pinecone API Key", description="API key for Pinecone"
    )
    AWS_ACCESS_KEY_ID: str = Field(..., description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., description="AWS secret access key")
    AWS_REGION: str = Field(..., description="AWS region")
    ENABLE_PROGRESS_BAR: bool = Field(
        True, description="Whether to enable progress bar for duckdb"
    )
    HST: str = Field(environ["HST"], description="Host for the database")
    USR: str = Field(environ["USR"], description="User for the database")
    PWD: SecretStr = Field(environ["PWD"], description="Password for the database")
    DB: str = Field(environ["DB"], description="Database name")
