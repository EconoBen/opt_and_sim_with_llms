"""Main entry point for the application."""

import streamlit as st

from src.embeddings.embeds_page import embeddings_page
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
    page = st.sidebar.radio("Go to", ["Embeddings", "Org Structure", "Ticketing"])

    if page == "Embeddings":
        embeddings_page()
    elif page == "Org Structure":
        generate_structure_page()
    elif page == "Ticketing":
        org_structure = generate_structure_page()
        generate_tickets_page(org_structure)


if __name__ == "__main__":
    main()
