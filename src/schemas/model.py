"""Sets schemas for embeddings model"""

from os import environ

from pydantic import BaseModel, Field


class ModelSettings(BaseModel):
    """Model settings"""

    MODEL_VERSION: str = Field(
        environ["MODEL_VERSION"],
        title="Model",
        description="Pre-trained word embeddings model",
    )

    class Config:
        """Model settings config"""

        env_file = ".env"
        title = "Model Settings"
        description = "Settings for the embeddings model"
