from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "Cenvi Drive Backend"
    APP_ENV: str = "local"
    APP_DEBUG: bool = True

    GOOGLE_SERVICE_ACCOUNT_FILE: str
    GOOGLE_DRIVE_SCOPES: str

    ROOT_DRIVE_FOLDER_ID: str
    COMPANY_PARENT_FOLDER_ID: str
    DATABASE_URL: str = Field(...)

    class Config:
        env_file = ".env"

settings = Settings()
