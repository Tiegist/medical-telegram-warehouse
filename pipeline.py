import subprocess
from pathlib import Path

from dagster import job, op


@op
def scrape_telegram_data():
    subprocess.run(["python", "src/scraper.py"], check=True)


@op
def load_raw_to_postgres():
    subprocess.run(["python", "src/load_raw.py"], check=True)


@op
def run_yolo_enrichment():
    subprocess.run(["python", "src/yolo_detect.py"], check=True)
    subprocess.run(["python", "src/load_yolo_results.py"], check=True)


@op
def run_dbt_transformations():
    dbt_dir = Path("medical_warehouse")
    subprocess.run(["dbt", "deps", "--project-dir", str(dbt_dir)], check=True)
    subprocess.run(["dbt", "run", "--project-dir", str(dbt_dir)], check=True)
    subprocess.run(["dbt", "test", "--project-dir", str(dbt_dir)], check=True)


@job
def medical_telegram_pipeline():
    scrape_telegram_data()
    load_raw_to_postgres()
    run_yolo_enrichment()
    run_dbt_transformations()


