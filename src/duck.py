"""DuckDB connection context manager."""

from typing import Any

import duckdb

from src.schemas.db_settings import DBSettings

db_settings = DBSettings()  # type: ignore


class DBDuck:
    """DuckDB connection context manager."""

    s3_region: str = db_settings.AWS_REGION
    s3_access_key_id: str = db_settings.AWS_ACCESS_KEY_ID
    s3_secret_access_key: str = db_settings.AWS_SECRET_ACCESS_KEY
    enable_progress_bar: bool = db_settings.ENABLE_PROGRESS_BAR
    db_path: str = db_settings.DUCKDB_PATH
    con: duckdb.DuckDBPyConnection

    def __enter__(self) -> duckdb.DuckDBPyConnection:
        """Enter context manager.

        Args:
        self: DBDuck object

        Returns:
        duckdb.DuckDBPyConnection: DuckDB connection object
        """
        self.con: duckdb.DuckDBPyConnection = duckdb.connect(self.db_path)
        usr: str = db_settings.USR
        hst: str = db_settings.HST
        db: str = db_settings.DB
        pwd: str = db_settings.PWD.get_secret_value()
        address: str = f"postgresql://{usr}:{pwd}@{hst}:5432/{db}"
        self.con.execute(
            f"""
				INSTALL httpfs;
				LOAD httpfs;
                INSTALL postgres;
                LOAD postgres;

                ATTACH {address} AS rds_dev (TYPE postgres);

				SET s3_region='{self.s3_region}';
				SET s3_access_key_id='{self.s3_access_key_id}';
				SET s3_secret_access_key='{self.s3_secret_access_key}';
				SET enable_progress_bar = {self.enable_progress_bar};
				"""
        )
        return self.con

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exit context manager.

        Args:
        self: DBDuck object
        exc_type: Exception type
        exc_value: Exception value
        traceback: Traceback

        Returns:
        None
        """
        self.con.close()
