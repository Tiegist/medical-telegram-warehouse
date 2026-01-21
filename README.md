# Medical Telegram Warehouse

End-to-end data pipeline for Ethiopian medical Telegram channels. This project follows the "10 Academy - KAIM 8 - Week 8" requirements and includes scraping, loading, dbt modeling, YOLO enrichment, an analytical API, and Dagster orchestration.

## Quickstart

1) Create a virtual environment and install dependencies:

```
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
```

2) Copy `config.env.example` to `.env` and fill in values:
- Telegram API credentials from `my.telegram.org`
- Postgres credentials

3) Start Postgres with Docker:

```
docker compose up -d postgres
```

## Task 1 - Scrape Telegram

```
python src/scraper.py --limit 200
```

Raw data lands in `data/raw/telegram_messages/YYYY-MM-DD/{channel}.json` and images in `data/raw/images/{channel}/{message_id}.jpg`.

## Task 2 - Load + dbt

Load raw JSON to Postgres:

```
python src/load_raw.py --truncate
```

Run dbt:

```
dbt deps --project-dir medical_warehouse
dbt run --project-dir medical_warehouse
dbt test --project-dir medical_warehouse
```

## Task 3 - YOLO Enrichment

```
python src/yolo_detect.py
python src/load_yolo_results.py --truncate
dbt run --project-dir medical_warehouse --select fct_image_detections
```

## Task 4 - FastAPI

```
uvicorn api.main:app --reload
```

Open `http://localhost:8000/docs`.

## Task 5 - Dagster

```
dagster dev -f pipeline.py


Open `http://localhost:3000`.

## Notes
- dbt profiles: `medical_warehouse/profiles.yml` expects env vars.
- Logs: `logs/` contains scraper logs.


