import argparse
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from src.config import settings


DATA_DIR = Path("data/raw/telegram_messages")
IMAGE_DIR = Path("data/raw/images")
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "scraper.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def _safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)


def _message_to_dict(message, channel_name: str, image_path: str | None):
    return {
        "message_id": message.id,
        "channel_name": channel_name,
        "message_date": message.date.isoformat() if message.date else None,
        "message_text": message.message or "",
        "has_media": bool(message.media),
        "image_path": image_path,
        "views": message.views or 0,
        "forwards": message.forwards or 0,
        "raw": message.to_dict(),
    }


async def _download_image(client: TelegramClient, message, channel_dir: Path) -> str | None:
    if not message.photo:
        return None
    channel_dir.mkdir(parents=True, exist_ok=True)
    image_path = channel_dir / f"{message.id}.jpg"
    if image_path.exists():
        return str(image_path)
    await client.download_media(message, file=image_path)
    return str(image_path)


async def scrape_channel(client: TelegramClient, channel: str, start_date: datetime | None, limit: int | None):
    safe_channel = _safe_name(channel)
    async for message in client.iter_messages(channel, limit=limit):
        if start_date and message.date and message.date < start_date:
            break
        try:
            image_path = await _download_image(client, message, IMAGE_DIR / safe_channel)
            msg_date = (message.date or datetime.now(timezone.utc)).date()
            out_dir = DATA_DIR / msg_date.isoformat()
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{safe_channel}.json"
            record = _message_to_dict(message, channel, image_path)
            with out_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except FloodWaitError as exc:
            logging.warning("Rate limited on %s. Sleeping %s seconds", channel, exc.seconds)
            await asyncio.sleep(exc.seconds + 1)
        except Exception as exc:
            logging.exception("Failed to process message %s from %s: %s", message.id, channel, exc)
    logging.info("Finished scraping channel: %s", channel)


async def main_async(channels: list[str], limit: int | None, since_days: int | None, start_date: str | None):
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise ValueError("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in environment.")

    resolved_channels = channels or settings.telegram_channels
    if not resolved_channels:
        raise ValueError("No channels provided. Set TELEGRAM_CHANNELS or use --channels.")

    if start_date:
        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    elif since_days:
        start_dt = datetime.now(timezone.utc) - timedelta(days=since_days)
    else:
        start_dt = None

    async with TelegramClient(settings.telegram_session, settings.telegram_api_id, settings.telegram_api_hash) as client:
        for channel in resolved_channels:
            logging.info("Scraping channel: %s", channel)
            await scrape_channel(client, channel, start_dt, limit)


def main():
    parser = argparse.ArgumentParser(description="Scrape Telegram channels to raw data lake.")
    parser.add_argument("--channels", nargs="*", default=[], help="Override channels list.")
    parser.add_argument("--limit", type=int, default=None, help="Limit messages per channel.")
    parser.add_argument("--since-days", type=int, default=None, help="Only messages in last N days.")
    parser.add_argument("--start-date", type=str, default=None, help="ISO date filter (YYYY-MM-DD).")
    args = parser.parse_args()

    asyncio.run(main_async(args.channels, args.limit, args.since_days, args.start_date))


if __name__ == "__main__":
    main()


