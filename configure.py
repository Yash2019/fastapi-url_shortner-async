from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    DATABASE_URL: str

    model_config=SettingsConfigDict(
        env_file='.env',
        extra='ignore'
    )

config = Setting()