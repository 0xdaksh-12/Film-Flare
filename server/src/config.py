from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str
    ACCESS_EXPIRE_MINUTES: int = 15
    REFRESH_EXPIRE_DAYS: int = 7
    COOKIE_TOKEN: str = "AuthToken"
    ENV: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    def __init__(self, **data):
        super().__init__(**data)

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"


Config = Settings()
