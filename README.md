# B9W8: Shipping a Data Product — Medical Telegram Warehouse

**Author:** Mariamawit Ewnetu Alemu  
**Program:** 10 Academy AI Mastery  
**Project:** From Raw Telegram Data to an Analytical API

This repository implements an end-to-end data product for Kara Solutions. It extracts public Telegram data from Ethiopian medical-related channels, stores raw messages and images in a data lake, loads the raw data into PostgreSQL, transforms it with dbt into a star schema, enriches images using YOLOv8, exposes analytical insights through FastAPI, and orchestrates the workflow with Dagster.

## Business Objective

Ethiopian medical and pharmaceutical businesses frequently use Telegram to advertise products, share availability updates, and engage customers. The goal of this project is to convert that unstructured Telegram activity into reliable analytical data that can answer business questions such as:

- What are the top mentioned medical products across channels?
- Which channels post most frequently?
- How does channel engagement vary over time?
- Which channels rely most on visual content?
- Do image categories provide additional analytical value?

## Architecture

```text
Telegram Channels
CheMed | Lobelia Cosmetics | Tikvah Pharma
        ↓
Telethon Scraper
        ↓
Raw Data Lake: JSON + Images
        ↓
PostgreSQL raw schema
        ↓
dbt staging + marts
        ↓
YOLOv8 image enrichment
        ↓
FastAPI analytical endpoints
        ↓
Dagster orchestration
```

## Repository Structure

```text
medical-telegram-warehouse/
├── .github/workflows/unittests.yml
├── api/
│   ├── main.py
│   ├── database.py
│   └── schemas.py
├── data/
│   ├── raw/
│   │   ├── telegram_messages/YYYY-MM-DD/channel_name.json
│   │   └── images/channel_name/message_id.jpg
│   └── processed/yolo_detections.csv
├── logs/
│   ├── scraper.log
│   └── yolo_detection.log
├── medical_warehouse/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/staging/
│   ├── models/marts/
│   └── tests/
├── src/
│   ├── scraper.py
│   ├── load_raw_to_postgres.py
│   ├── yolo_detect.py
│   └── load_yolo_to_postgres.py
├── tests/
├── pipeline.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Task Coverage

### Task 1 — Data Scraping and Collection

- `src/scraper.py` uses Telethon-based scraping logic.
- Target channels include CheMed, Lobelia Cosmetics, and Tikvah Pharma.
- Raw messages are stored in `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`.
- Images are stored in `data/raw/images/{channel_name}/{message_id}.jpg`.
- Logs are written to `logs/scraper.log`.

Collected fields include:

- `message_id`
- `channel_name`
- `message_date`
- `message_text`
- `views`
- `forwards`
- `has_media`
- `image_path`

### Task 2 — dbt Transformation

- `src/load_raw_to_postgres.py` loads raw JSON into PostgreSQL.
- dbt project is located in `medical_warehouse/`.
- Staging model: `stg_telegram_messages.sql`.
- Mart models:
  - `dim_channels.sql`
  - `dim_dates.sql`
  - `fct_messages.sql`
- dbt tests include unique, not-null, relationships, and custom SQL tests.

### Task 3 — YOLOv8 Image Enrichment

- `src/yolo_detect.py` uses YOLOv8 nano: `yolov8n.pt`.
- Detection results are saved to `data/processed/yolo_detections.csv`.
- Image categories implemented:
  - `promotional`
  - `product_display`
  - `lifestyle`
  - `other`
- `models/marts/fct_image_detections.sql` joins YOLO results with `fct_messages`.

### Task 4 — FastAPI Analytical API

FastAPI files are located in `api/`.

Implemented endpoints:

```text
GET /api/reports/top-products?limit=10
GET /api/channels/{channel_name}/activity
GET /api/search/messages?query=paracetamol&limit=20
GET /api/reports/visual-content
```

Run the API:

```bash
uvicorn api.main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

### Task 5 — Dagster Orchestration

The orchestration file is `pipeline.py`.

Defined Dagster ops:

- `scrape_telegram_data`
- `load_raw_to_postgres`
- `run_dbt_transformations`
- `run_yolo_enrichment`

A daily schedule is defined using Dagster `ScheduleDefinition`.

Run Dagster:

```bash
dagster dev -f pipeline.py
```

Open Dagster UI:

```text
http://localhost:3000
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:

```text
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=medical_warehouse
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start PostgreSQL with Docker if available:

```bash
docker compose up -d
```

Or use a local PostgreSQL installation.

## Run the Pipeline Manually

```bash
python src/scraper.py
python src/load_raw_to_postgres.py
cd medical_warehouse
dbt debug
dbt run
dbt test
cd ..
python src/yolo_detect.py
python src/load_yolo_to_postgres.py
uvicorn api.main:app --reload
```

## Testing

```bash
pytest -q
```

GitHub Actions CI is configured in `.github/workflows/unittests.yml`.

## Git Workflow Evidence

Recommended task branches:

```text
task-1-scraping
task-2-dbt
task-3-yolo
task-4-api
task-5-dagster
```

Each task branch should be merged into `main` through a Pull Request.

## Notes

The repository includes small sample raw data, images, logs, and YOLO detection CSV evidence so evaluators can verify the expected structure without requiring access to private Telegram credentials.
