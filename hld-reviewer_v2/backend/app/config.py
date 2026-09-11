from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GitHub Models inference endpoint (OpenAI-compatible).
    # Create a fine-grained PAT with "models: read" permission -> https://github.com/settings/tokens
    github_token: str = ""
    github_models_endpoint: str = "https://models.inference.ai.azure.com/chat/completions"

    # Cheap model for structural/checklist screening (Stage 2)
    cheap_model: str = "gpt-4o-mini"
    # Stronger model for escalated deep-reasoning review (Stage 3)
    strong_model: str = "gpt-4o"

    # Storage for extracted chunk hashes, used for diff-based re-review
    storage_dir: str = "./storage"

    class Config:
        env_file = ".env"


settings = Settings()
