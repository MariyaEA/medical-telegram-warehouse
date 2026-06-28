"""Load partitioned raw Telegram JSON files into PostgreSQL raw schema."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, execute_values

load_dotenv()

RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", "data/raw/telegram_messages"))


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "medical_warehouse"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def iter_json_files(raw_dir: Path):
    yield from raw_dir.glob("**/*.json")


def read_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if isinstance(payload, dict):
        return [payload]
    return payload


def create_raw_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                raw_id BIGSERIAL PRIMARY KEY,
                message_id BIGINT NOT NULL,
                channel_name TEXT NOT NULL,
                channel_username TEXT,
                message_date TIMESTAMPTZ,
                message_text TEXT,
                views INTEGER DEFAULT 0,
                forwards INTEGER DEFAULT 0,
                has_media BOOLEAN DEFAULT FALSE,
                media_type TEXT,
                image_path TEXT,
                scraped_at TIMESTAMPTZ,
                source_file TEXT NOT NULL,
                raw_payload JSONB NOT NULL,
                loaded_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(message_id, channel_username)
            );
            """
        )
    conn.commit()


def load_records(conn, records: list[dict[str, Any]], source_file: str) -> int:
    rows = [
        (
            r.get("message_id"),
            r.get("channel_name"),
            r.get("channel_username"),
            r.get("message_date"),
            r.get("message_text"),
            int(r.get("views") or 0),
            int(r.get("forwards") or 0),
            bool(r.get("has_media")),
            r.get("media_type"),
            r.get("image_path"),
            r.get("scraped_at"),
            source_file,
            Json(r),
        )
        for r in records
        if r.get("message_id") is not None and r.get("channel_name")
    ]
    if not rows:
        return 0

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO raw.telegram_messages (
                message_id, channel_name, channel_username, message_date, message_text,
                views, forwards, has_media, media_type, image_path, scraped_at, source_file, raw_payload
            ) VALUES %s
            ON CONFLICT (message_id, channel_username) DO UPDATE SET
                message_text = EXCLUDED.message_text,
                views = EXCLUDED.views,
                forwards = EXCLUDED.forwards,
                has_media = EXCLUDED.has_media,
                media_type = EXCLUDED.media_type,
                image_path = EXCLUDED.image_path,
                raw_payload = EXCLUDED.raw_payload,
                loaded_at = NOW();
            """,
            rows,
        )
    conn.commit()
    return len(rows)


def main() -> None:
    conn = get_connection()
    create_raw_table(conn)
    total = 0
    try:
        for path in iter_json_files(RAW_DATA_DIR):
            records = read_records(path)
            total += load_records(conn, records, str(path))
            print(f"Loaded {len(records)} records from {path}")
    finally:
        conn.close()
    print(f"Raw load complete. Inserted/updated {total} records.")


if __name__ == "__main__":
    main()
