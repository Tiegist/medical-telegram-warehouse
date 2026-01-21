import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import settings


def _postgres_url():
    return (
        f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )


def load_yolo(csv_path: Path, truncate: bool):
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing YOLO CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    if df.empty:
        print("No YOLO results found to load.")
        return

    engine = create_engine(_postgres_url())
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema_raw}"))
        if truncate:
            conn.execute(
                text(f"DROP TABLE IF EXISTS {settings.db_schema_raw}.yolo_detections")
            )

    df.to_sql(
        "yolo_detections",
        engine,
        schema=settings.db_schema_raw,
        if_exists="append",
        index=False,
    )
    print(f"Loaded {len(df)} detections into {settings.db_schema_raw}.yolo_detections")


def main():
    parser = argparse.ArgumentParser(description="Load YOLO CSV results into Postgres.")
    parser.add_argument("--csv-path", default="data/processed/yolo_detections.csv")
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()

    load_yolo(Path(args.csv_path), args.truncate)


if __name__ == "__main__":
    main()


