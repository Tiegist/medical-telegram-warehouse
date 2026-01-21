import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _get_env(name, default=None, required=False, cast=str):
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise ValueError(f"Missing required env var: {name}")
    if value is None:
        return None
    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid value for {name}: {value}") from exc


@dataclass(frozen=True)
class Settings:
    telegram_api_id: int
    telegram_api_hash: str
    telegram_session: str
    telegram_channels: list[str]
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    db_schema_raw: str
    db_schema_staging: str
    db_schema_marts: str
    yolo_model: str


settings = Settings(
    telegram_api_id=_get_env("TELEGRAM_API_ID", required=False, cast=int) or 0,
    telegram_api_hash=_get_env("TELEGRAM_API_HASH", default=""),
    telegram_session=_get_env("TELEGRAM_SESSION", default="medical-telegram-session"),
    telegram_channels=[
        c.strip()
        for c in _get_env("TELEGRAM_CHANNELS", default="").split(",")
        if c.strip()
    ],
    postgres_host=_get_env("POSTGRES_HOST", default="localhost"),
    postgres_port=_get_env("POSTGRES_PORT", default=5432, cast=int),
    postgres_db=_get_env("POSTGRES_DB", default="medical_warehouse"),
    postgres_user=_get_env("POSTGRES_USER", default="postgres"),
    postgres_password=_get_env("POSTGRES_PASSWORD", default="postgres"),
    db_schema_raw=_get_env("DB_SCHEMA_RAW", default="raw"),
    db_schema_staging=_get_env("DB_SCHEMA_STAGING", default="staging"),
    db_schema_marts=_get_env("DB_SCHEMA_MARTS", default="marts"),
    yolo_model=_get_env("YOLO_MODEL", default="yolov8n.pt"),
)


