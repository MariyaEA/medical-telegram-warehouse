"""Telegram scraping pipeline for Ethiopian medical product channels.

Task 1 evidence:
- Telethon-based scraping logic
- Targets CheMed, Lobelia Cosmetics, and Tikvah Pharma
- Saves raw JSON to a partitioned data lake
- Downloads images by channel
- Logs scraping activity and errors
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
from telethon import TelegramClient, errors

load_dotenv()

CHANNELS = {
    "chemed": "CheMed Telegram Channel",
    "lobelia_cosmetics": "Lobelia Cosmetics",
    "tikvah_pharma": "Tikvah Pharma",
}

RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", "data/raw/telegram_messages"))
RAW_IMAGE_DIR = Path(os.getenv("RAW_IMAGE_DIR", "data/raw/images"))
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
SCRAPE_LIMIT = int(os.getenv("SCRAPE_LIMIT_PER_CHANNEL", "100"))


@dataclass
class TelegramMessageRecord:
    message_id: int
    channel_name: str
    channel_username: str
    message_date: str
    message_text: Optional[str]
    views: int
    forwards: int
    has_media: bool
    media_type: Optional[str]
    image_path: Optional[str]
    scraped_at: str


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / "scraper.log",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    logging.getLogger().addHandler(console)


def normalize_channel_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("/", "_")


def partition_path(run_date: datetime, channel_slug: str) -> Path:
    return RAW_DATA_DIR / run_date.strftime("%Y-%m-%d") / f"{channel_slug}.json"


async def download_photo_if_present(client: TelegramClient, message, channel_slug: str) -> Optional[str]:
    if not getattr(message, "photo", None):
        return None

    channel_dir = RAW_IMAGE_DIR / channel_slug
    channel_dir.mkdir(parents=True, exist_ok=True)
    image_path = channel_dir / f"{message.id}.jpg"

    try:
        downloaded = await client.download_media(message, file=str(image_path))
        return downloaded
    except FileNotFoundError as exc:
        logging.error("Missing media file for %s/%s: %s", channel_slug, message.id, exc)
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to download media for %s/%s: %s", channel_slug, message.id, exc)
    return None


async def scrape_channel(client: TelegramClient, channel_username: str, channel_name: str, limit: int) -> list[dict]:
    channel_slug = normalize_channel_name(channel_username)
    records: list[dict] = []
    logging.info("Starting scrape for channel=%s limit=%s", channel_username, limit)

    try:
        entity = await client.get_entity(channel_username)
        async for message in client.iter_messages(entity, limit=limit):
            image_path = await download_photo_if_present(client, message, channel_slug)
            media_type = type(message.media).__name__ if message.media else None
            record = TelegramMessageRecord(
                message_id=message.id,
                channel_name=channel_name,
                channel_username=channel_username,
                message_date=message.date.astimezone(timezone.utc).isoformat() if message.date else None,
                message_text=message.message,
                views=int(message.views or 0),
                forwards=int(message.forwards or 0),
                has_media=bool(message.media),
                media_type=media_type,
                image_path=image_path,
                scraped_at=datetime.now(timezone.utc).isoformat(),
            )
            records.append(asdict(record))
    except errors.FloodWaitError as exc:
        logging.error("Telegram rate limit for %s. Retry after %s seconds", channel_username, exc.seconds)
    except (errors.ChannelInvalidError, errors.ChannelPrivateError, ValueError) as exc:
        logging.error("Cannot access channel %s: %s", channel_username, exc)
    except ConnectionError as exc:
        logging.error("Network issue while scraping %s: %s", channel_username, exc)
    except Exception as exc:  # noqa: BLE001
        logging.exception("Unexpected scraping error for %s: %s", channel_username, exc)

    logging.info("Finished scrape for channel=%s records=%s", channel_username, len(records))
    return records


def write_json_partition(records: Iterable[dict], run_date: datetime, channel_slug: str) -> Path:
    output_path = partition_path(run_date, channel_slug)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(list(records), file, ensure_ascii=False, indent=2)
    logging.info("Wrote raw JSON partition: %s", output_path)
    return output_path


async def main() -> None:
    setup_logging()
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")

    if not api_id or not api_hash:
        raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")

    run_date = datetime.now(timezone.utc)
    async with TelegramClient("medical_telegram_session", int(api_id), api_hash) as client:
        if phone:
            await client.start(phone=phone)
        for username, display_name in CHANNELS.items():
            records = await scrape_channel(client, username, display_name, SCRAPE_LIMIT)
            write_json_partition(records, run_date, normalize_channel_name(username))


if __name__ == "__main__":
    asyncio.run(main())
