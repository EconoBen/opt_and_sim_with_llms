"""This module contains the Streamlit page for the embeddings pipeline."""

from pathlib import Path

import streamlit as st
from polars import DataFrame, concat

from src.duck import DBDuck
from src.embeddings.embed_data import EmbedsPipeline
from src.query_db import execute_query
from src.schemas.db_settings import DBSettings
from src.schemas.model import ModelSettings
from src.schemas.sql import SQLModel

model_settings = ModelSettings()  # type: ignore
db_settings = DBSettings()  # type: ignore
sql_model = SQLModel()  # type: ignore


def embeddings_page() -> None:
    st.title("Embeddings Pipeline")

    if "pipeline_run" not in st.session_state:
        st.session_state.pipeline_run = False

    if "job_embeds" not in st.session_state:
        st.session_state.job_embeds = None

    if "skills" not in st.session_state:
        st.session_state.skills = None

    model_version = st.sidebar.selectbox(
        "Select an embeddings model:",
        options=["all-MiniLM-L6-v2", "all-mpnet-base-v2", "paraphrase-MiniLM-L6-v2"],
        index=0,
    )

    if model_version not in [
        "all-MiniLM-L6-v2",
        "all-mpnet-base-v2",
        "paraphrase-MiniLM-L6-v2",
    ]:
        st.error("Invalid model version selected.")
        return

    is_sample = st.sidebar.radio("Sample the data?", options=["Yes", "No"], index=0)

    if st.sidebar.button("Run Pipeline"):
        with st.spinner("Running embeddings pipeline..."):
            pipeline = EmbedsPipeline(model_version)
            pipeline.run(is_sample == "Yes")
            st.success("Embeddings pipeline completed successfully!")
            st.session_state.pipeline = pipeline
            st.session_state.pipeline_run = True

    if st.session_state.pipeline_run:
        jobtitle: str = st.text_input("Enter the name of a job")

        if st.button("Find Similar Jobs"):
            with st.spinner("Finding similar jobs..."):
                jb_df: DataFrame = DataFrame({"jobtitle": [jobtitle]})
                embeds: DataFrame = st.session_state.pipeline.embed_data(
                    jb_df, "jobtitle"
                )
                st.session_state.job_embeds = concat([jb_df, embeds], how="horizontal")
                st.success("Similar jobs found!")

            if st.session_state.job_embeds is not None:
                with DBDuck() as quack:
                    quack.register("j_embeds", st.session_state.job_embeds)
                    query_result = DataFrame(
                        quack.execute("""
                        WITH job_embeds_cte AS (
                            SELECT jobtitle, jobtitle_embeddings
                            FROM j_embeds
                        )
                        SELECT
                            job_embeds_cte.jobtitle AS entered_job,
                            onet.ONET_ONETSOC_CODE,
                            onet.ONET_TITLES AS similar_job,
                            list_cosine_similarity(job_embeds_cte.jobtitle_embeddings, onet.TITLE_EMBEDDINGS) AS similarity,
                            onet.MEDIAN_SALARY AS median_salary
                        FROM
                            job_embeds_cte
                            CROSS JOIN onet_with_embeddings AS onet
                        ORDER BY similarity DESC
                        LIMIT 5
                    """).fetch_arrow_table()
                    )
                    st.write("Top 5 Similar Job Titles:")
                    st.table(query_result)
                    st.session_state.skills = query_result[
                        "ONET_ONETSOC_CODE"
                    ].to_list()

                if st.session_state.skills is not None:
                    with st.spinner("Let's get a little more specific..."):
                        st.write("Skills Asscoiated with the Top 5 Similar Job Titles:")
                        path = Path("src/sql/get_skills_by_onet.sql")
                        execute_query(
                            path,  # type: ignore
                            data=None,
                            params={"ONET_CODE": st.session_state.skills},
                        )
                        st.table(DataFrame(query_result))
