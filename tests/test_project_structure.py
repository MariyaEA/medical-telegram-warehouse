from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_files_exist():
    required = [
        "src/scraper.py",
        "src/load_raw_to_postgres.py",
        "medical_warehouse/dbt_project.yml",
        "medical_warehouse/models/staging/stg_telegram_messages.sql",
        "medical_warehouse/models/marts/dim_channels.sql",
        "medical_warehouse/models/marts/dim_dates.sql",
        "medical_warehouse/models/marts/fct_messages.sql",
        "medical_warehouse/tests/assert_no_future_messages.sql",
        "medical_warehouse/tests/assert_positive_views.sql",
    ]
    for relative_path in required:
        assert (ROOT / relative_path).exists(), f"Missing {relative_path}"


def test_sample_data_lake_exists():
    assert (ROOT / "data/raw/telegram_messages/2026-06-28/chemed.json").exists()
    assert (ROOT / "data/raw/images/chemed").exists()
