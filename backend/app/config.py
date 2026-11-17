from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration lue depuis les variables d'environnement et le fichier .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Bureau IA"
    database_url: str = "sqlite:///./data/deskpilot.db"
    uploads_dir: str = "./data/uploads"
    anthropic_api_key: str = ""


def get_settings() -> Settings:
    return Settings()
