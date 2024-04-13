"""Generic function to query the DuckDB database."""

from pathlib import PosixPath

from polars import DataFrame

from src.duck import DBDuck


def execute_query(
    query: PosixPath | str,
    data: DataFrame | None = None,
    params: dict[str, int | str] | None = None,
) -> DataFrame:
    """Generic function to query the DuckDB database.
    Args:
        query (str): SQL query string
        data (DataFrame | None): DataFrame to be used as parameters for the query
        params (dict | None): Additional parameters to be passed to the query
    Returns:
        DataFrame: Data from the query
    """
    with DBDuck() as quack:
        if isinstance(data, DataFrame):
            quack.register("data", data)

        query = query.read_text() if isinstance(query, PosixPath) else query
        return DataFrame(
            quack.execute(query, params).fetch_arrow_table(),
            orient="row",
        )
