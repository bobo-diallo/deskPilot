from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration lue depuis les variables d'environnement et le fichier .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Bureau IA"
    database_url: str = "sqlite:///./data/deskpilot.db"
    uploads_dir: str = "./data/uploads"
    exports_dir: str = "./data/exports"  # CSV produits par l'agent après approbation
    # Dossier des rapports d'évaluation (Markdown), lus en lecture seule par l'API.
    evaluation_reports_dir: str = "../docs/evaluation"
    anthropic_api_key: str = ""
    # Taille du modèle Whisper : tiny, base, small… (plus gros = plus juste mais plus lent)
    whisper_model_size: str = "small"


def get_settings() -> Settings:
    return Settings()
