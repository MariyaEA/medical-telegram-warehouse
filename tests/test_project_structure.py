from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_task_files_exist():
    required = [
        "src/scraper.py",
        "src/load_raw_to_postgres.py",
        "src/yolo_detect.py",
        "src/load_yolo_to_postgres.py",
        "api/main.py",
        "api/database.py",
        "api/schemas.py",
        "pipeline.py",
        "medical_warehouse/dbt_project.yml",
        "medical_warehouse/models/staging/stg_telegram_messages.sql",
        "medical_warehouse/models/marts/dim_channels.sql",
        "medical_warehouse/models/marts/dim_dates.sql",
        "medical_warehouse/models/marts/fct_messages.sql",
        "medical_warehouse/models/marts/fct_image_detections.sql",
    ]
    for relative_path in required:
        assert (ROOT / relative_path).exists(), f"Missing {relative_path}"


def test_raw_data_lake_evidence_exists():
    assert (ROOT / "data/raw/telegram_messages/2026-06-28/chemed.json").exists()
    assert (ROOT / "data/raw/images/chemed").exists()
    assert (ROOT / "logs/scraper.log").exists()


def test_api_endpoint_paths_present():
    source = (ROOT / "api/main.py").read_text()
    assert "/api/reports/top-products" in source
    assert "/api/channels/{channel_name}/activity" in source
    assert "/api/search/messages" in source
    assert "/api/reports/visual-content" in source


def test_dagster_ops_present():
    source = (ROOT / "pipeline.py").read_text()
    for op_name in [
        "scrape_telegram_data",
        "load_raw_to_postgres",
        "run_dbt_transformations",
        "run_yolo_enrichment",
        "ScheduleDefinition",
    ]:
        assert op_name in source
