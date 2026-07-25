import os

from pathlib import Path
from fastapi import HTTPException
from pydantic_settings import BaseSettings
from pydantic import field_validator, AmqpDsn
from dotenv import load_dotenv
from starlette import status

load_dotenv()


class Settings(BaseSettings):
    # Broker + taskiq
    BROKER_URL: str
    # DataBase
    DATABASE_URL: str
    # Mail SMTP
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 465
    MAIL_SERVER: str
    # Redis cache
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_db_url(cls, v: str):
        if not v:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return v

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


class SecuritySettings(BaseSettings):
    # JWT
    SECRET_KEY: str  # python -c "import secrets; print(secrets.token_hex(32))"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60      # Короткий срок
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7         # Долгий срок для обновления

    # База данных
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

security_settings = SecuritySettings()
