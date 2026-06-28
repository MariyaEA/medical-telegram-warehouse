# B9W8: Shipping a Data Product — Medical Telegram Warehouse

This repository is the interim submission for **B9W8: Shipping a Data Product: From Raw Telegram Data to an Analytical Warehouse**. It implements Task 1 and Task 2: Telegram scraping, raw data lake storage, raw loading into PostgreSQL, and dbt-based dimensional modeling.

## Business Objective

Kara Solutions needs an analytical data platform for Ethiopian medical and pharmaceutical Telegram channels. The platform collects raw public Telegram messages and turns them into trusted warehouse tables that can answer questions about product mentions, posting activity, channel behavior, views, forwards, and image usage.

## Data Sources

The scraper targets these public Telegram channels:

- CheMed Telegram Channel
- Lobelia Cosmetics
- Tikvah Pharma

Additional Ethiopian medical channels can be added in `src/scraper.py` through the `CHANNELS` list.

## Repository Structure

```text
medical-telegram-warehouse/
├── src/
│   ├── scraper.py
│   └── load_raw_to_postgres.py
├── data/raw/
│   ├── telegram_messages/YYYY-MM-DD/channel_name.json
│   └── images/channel_name/message_id.jpg
├── logs/
│   └── scraper.log
└── medical_warehouse/
    ├── dbt_project.yml
    ├── profiles.yml
    ├── models/staging/stg_telegram_messages.sql
    ├── models/marts/dim_channels.sql
    ├── models/marts/dim_dates.sql
    ├── models/marts/fct_messages.sql
    └── tests/
```

## Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the environment template and fill in your private credentials:

```bash
cp .env.example .env
```

`.env` is intentionally ignored by Git and must never be committed.

## Run PostgreSQL

```bash
docker compose up -d
```

## Task 1: Telegram Scraping

Run the scraper:

```bash
python src/scraper.py
```

The scraper:

- Uses Telethon.
- Extracts `message_id`, `channel_name`, `message_date`, `message_text`, `views`, `forwards`, `has_media`, `media_type`, and `image_path`.
- Writes raw JSON files to `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`.
- Downloads images to `data/raw/images/channel_name/message_id.jpg`.
- Writes logs to `logs/scraper.log`.

A small sample raw data lake is included for grading visibility.

## Task 2: Raw Loading and dbt Transformation

Load raw JSON into PostgreSQL:

```bash
python src/load_raw_to_postgres.py
```

Run dbt:

```bash
cd medical_warehouse
dbt run
dbt test
```

## Warehouse Design

The dbt models implement a star schema.

### Dimensions

- `dim_channels`: one row per Telegram channel, including channel type, first/last post date, total posts, and average views.
- `dim_dates`: calendar dimension with day, week, month, quarter, year, and weekend fields.

### Fact Table

- `fct_messages`: one row per Telegram message, linked to `dim_channels` and `dim_dates`. It includes message text, message length, views, forwards, and image flags.

## Data Quality Tests

The project includes dbt schema tests and custom SQL tests:

- Primary keys are `unique` and `not_null`.
- Foreign keys are tested with `relationships`.
- `assert_no_future_messages.sql` checks that message dates are not in the future.
- `assert_positive_views.sql` checks that view counts are non-negative.
