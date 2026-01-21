import argparse
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import settings


def _postgres_url():
    return (
        f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )


def _load_records(data_dir: Path) -> list[dict]:
    records = []
    for json_file in data_dir.rglob("*.json"):
        with json_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
    return records


def _normalize(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["message_date"] = pd.to_datetime(df.get("message_date"))
    df["views"] = pd.to_numeric(df.get("views"), errors="coerce").fillna(0).astype(int)
    df["forwards"] = pd.to_numeric(df.get("forwards"), errors="coerce").fillna(0).astype(int)
    df["has_media"] = df.get("has_media").fillna(False).astype(bool)
    df["message_text"] = df.get("message_text").fillna("")
    df["channel_name"] = df.get("channel_name").fillna("unknown")
    return df


def load_raw(data_dir: Path, truncate: bool):
    records = _load_records(data_dir)
    df = _normalize(records)
    if df.empty:
        print("No records found to load.")
        return

    engine = create_engine(_postgres_url())
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema_raw}"))
        if truncate:
            conn.execute(
                text(f"DROP TABLE IF EXISTS {settings.db_schema_raw}.telegram_messages")
            )

    df.to_sql(
        "telegram_messages",
        engine,
        schema=settings.db_schema_raw,
        if_exists="append",
        index=False,
    )
    print(f"Loaded {len(df)} records into {settings.db_schema_raw}.telegram_messages")


def main():
    parser = argparse.ArgumentParser(description="Load raw JSON files into Postgres.")
    parser.add_argument("--data-dir", default="data/raw/telegram_messages")
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()

    load_raw(Path(args.data_dir), args.truncate)


if __name__ == "__main__":
    main()


