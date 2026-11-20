import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./nexuscorp.db"
    jwt_secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_initial_password: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
settings = Settings()
