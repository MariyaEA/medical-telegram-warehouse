"""Dagster orchestration for the medical Telegram warehouse pipeline."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dagster import Definitions, ScheduleDefinition, job, op

PROJECT_ROOT = Path(__file__).resolve().parent


def run_command(command: list[str], cwd: Path = PROJECT_ROOT) -> None:
    """Run a command and fail the Dagster op if the command fails."""
    completed = subprocess.run(command, cwd=cwd, check=False, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(command)}")


@op
def scrape_telegram_data() -> str:
    """Run the Telethon scraper and populate the raw Telegram data lake."""
    run_command([sys.executable, "src/scraper.py"])
    return "scraping_completed"


@op
def load_raw_to_postgres(previous_step: str) -> str:
    """Load raw Telegram JSON files from the data lake into PostgreSQL raw schema."""
    run_command([sys.executable, "src/load_raw_to_postgres.py"])
    return "raw_loading_completed"


@op
def run_dbt_transformations(previous_step: str) -> str:
    """Run dbt models and tests to build the analytical warehouse."""
    run_command(["dbt", "run"], cwd=PROJECT_ROOT / "medical_warehouse")
    run_command(["dbt", "test"], cwd=PROJECT_ROOT / "medical_warehouse")
    return "dbt_completed"


@op
def run_yolo_enrichment(previous_step: str) -> str:
    """Run YOLOv8 image enrichment and load detection results into PostgreSQL."""
    run_command([sys.executable, "src/yolo_detect.py"])
    run_command([sys.executable, "src/load_yolo_to_postgres.py"])
    return "yolo_completed"


@job
def medical_telegram_pipeline():
    """End-to-end job graph for scraping, loading, dbt transformation, and YOLO enrichment."""
    scraped = scrape_telegram_data()
    loaded = load_raw_to_postgres(scraped)
    transformed = run_dbt_transformations(loaded)
    run_yolo_enrichment(transformed)


daily_medical_telegram_schedule = ScheduleDefinition(
    job=medical_telegram_pipeline,
    cron_schedule="0 6 * * *",
    name="daily_medical_telegram_pipeline",
    description="Runs the Telegram medical data pipeline every morning.",
)


defs = Definitions(
    jobs=[medical_telegram_pipeline],
    schedules=[daily_medical_telegram_schedule],
)
