"""Main entry point for the application."""

import streamlit as st

from src.embeddings.embeds_page import embeddings_page
from src.optimization.optimization_page import generate_optimization_page
from src.org_structure.generate_page import generate_structure_page
from src.schemas.db_settings import DBSettings
from src.schemas.model import ModelSettings
from src.schemas.sql import SQLModel
from src.ticketing.ticketing_page import generate_tickets_page

model_settings = ModelSettings()  # type: ignore
db_settings = DBSettings()  # type: ignore
sql_model = SQLModel()  # type: ignore


### choose which page to run in streamlit
def main() -> None:
    """Main entry point for the application."""

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to", ["Embeddings", "Org Structure", "Ticketing", "Optimization"]
    )

    if page == "Embeddings":
        embeddings_page()
    elif page == "Org Structure":
        generate_structure_page()
    elif page == "Ticketing":
        org_structure = generate_structure_page()
        generate_tickets_page(org_structure)
    elif page == "Optimization":
        org_structure = generate_structure_page()
        if "org_structure" not in locals():
            st.warning("Please generate the org structure first.")
        else:
            generate_optimization_page(org_structure)


if __name__ == "__main__":
    main()
