"""Script to embed provided text data into a vector space using pre-trained word embeddings."""

from pprint import pprint

from polars import DataFrame, concat
from sentence_transformers import SentenceTransformer  # type: ignore
from tqdm import tqdm  # type: ignore

from src.logger import setup_logging
from src.query_db import execute_query
from src.schemas.db_settings import DBSettings
from src.schemas.model import ModelSettings
from src.schemas.sql import SQLModel

model_settings = ModelSettings()  # type: ignore
db_settings = DBSettings()  # type: ignore
sql_model = SQLModel()  # type: ignore


class EmbedsPipeline:
    """Embeddings pipeline."""

    logger, log_time_date = setup_logging(
        logger_name="my_logger",
    )

    def __init__(self, model_version: str) -> None:
        """Initialize the embeddings pipeline."""

        self.logger.info("Initializing embeddings pipeline.")
        self.model_version: str = model_version

    @log_time_date
    def embed_data(
        self, data: DataFrame, column: str, batch_size: int = 100
    ) -> DataFrame:
        """Embed data into a vector space using sentence-transformers.
        Args:
            data (DataFrame): Data to embed
            column (str): Column to embed
            batch_size (int): Batch size for embedding
        Returns:
            DataFrame: DataFrame with a single column containing arrays of floats
        """
        model = SentenceTransformer(self.model_version)
        embeds: list[list[float]] = []

        column_data: list[float] = data.get_column(column).to_list()

        for idx in tqdm(
            range(0, len(column_data), batch_size),
            total=len(column_data) // batch_size + 1,
            desc=f"Embedding {column} data",
        ):
            batch_embeds = model.encode(
                column_data[idx : idx + batch_size],
                convert_to_numpy=True,
                show_progress_bar=True,
            )
            embeds.extend(batch_embeds.tolist())

        return DataFrame({f"{column}_embeddings": embeds})

    @log_time_date
    def run(self, sample_data: bool) -> None:
        """Run the embeddings pipeline to embed the ONET data into a vector space.
        First, the ONET data is queried from the database.
        Then, the title and description columns are embedded into a vector space using pre-trained word embeddings.
        Finally, the embedded data is written as a table in the database.

        Args:
            sample (bool): Whether to sample the data before embedding

        Returns:
            None
        """

        onet_data: DataFrame = execute_query(
            sql_model.ONET_QUERY, data=None, params={"lmt": 100 if sample_data else 0}
        )

        self.logger.info("Beginning embeddings pipeline...")
        embeddings: dict[str, DataFrame] = {}
        for embeds_column in ["titles", "descriptions"]:
            self.logger.info(f"Embedding {embeds_column} data...")
            embeds_data: DataFrame = self.embed_data(
                data=onet_data, column=embeds_column
            )
            embeddings[embeds_column] = embeds_data

        # Concatenate the title and description embeddings DataFrames
        embeddings_data = concat(
            [
                onet_data,
                embeddings["titles"],
                embeddings["descriptions"],
            ],
            how="horizontal",
        )

        execute_query(
            sql_model.EMBEDS_QUERY,
            data=embeddings_data,
            params={"model_version": self.model_version},
        )

        self.logger.info("Embeddings saved!")

        # Show the new table with embeddings
        query = """SELECT * FROM onet_with_embeddings LIMIT 5;"""
        pprint(execute_query(query))
