from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)

    SECRET_KEY: str = "fallback-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "postgresql://vsadmin:vspass@localhost:5432/valueseeker"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "ad123"
    SUPERADMIN_PASSWORD: str = "super123"


settings = Settings()
