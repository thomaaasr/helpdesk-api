from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracoes(BaseSettings):
    # Lê do ambiente e, se existir, do arquivo .env. Sem DATABASE_URL a API nem sobe.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    database_url_teste: str | None = None

    jwt_secret: str
    jwt_expira_minutos: int = 60


configuracoes = Configuracoes()
