from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Neo4j
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # App
    secret_key: str = "change-me-in-production"
    admin_api_key: str = "admin-secret"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Bot trigger prefixes (WhatsApp only)
    bot_prefixes: list[str] = ["!", "/"]
    bot_name: str = "familybot"


settings = Settings()
