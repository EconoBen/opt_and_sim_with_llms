"""Schemas for accessing data from the database."""

from os import environ
from pathlib import Path, PosixPath

from pydantic import BaseModel, Field


class SQLModel(BaseModel):
    """SQL Model"""

    ONET_QUERY: PosixPath = Field(
        Path(environ["ONET_QUERY"]),
        title="ONET Query",
        description="Query that retrieves data from the ONET database",
    )

    EMBEDS_QUERY: PosixPath = Field(
        Path(environ["EMBEDS_QUERY"]),
        title="Embeddings Query",
        description="Query that writes embeddings data to duckdb table.",
    )

    ### read in the .env file
    class Config:
        """SQL Model config"""

        env_file = ".env"
        title = "SQL Settings"
        description = "Settings for the SQL model"
