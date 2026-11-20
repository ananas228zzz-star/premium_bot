import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

import lang_store
import texts
from database import Database
from keyboards.inline import open_app_kb

MSK = timezone(timedelta(hours=3))
CHECK_INTERVAL = 600
NIGHT_FROM = 0
NIGHT_TO = 9
SEND_PAUSE = 0.1
STAGES = ((3, 72 * 3600), (2, 24 * 3600), (1, 3 * 3600))
MIN_DELAY = 3 * 3600


def is_night() -> bool:
    hour = datetime.now(MSK).hour
    return NIGHT_FROM <= hour < NIGHT_TO


def target_stage(elapsed: int) -> int:
    for stage, seconds in STAGES:
        if elapsed >= seconds:
            return stage
    return 0


async def process(bot: Bot, db: Database) -> None:
    now = int(time.time())
    rows = await db.get_reminder_candidates(now - MIN_DELAY)
    for row in rows:
        user_id = row["user_id"]
        last_activity = row["last_activity"]
        stage = target_stage(now - last_activity)
        if stage <= row["remind_stage"]:
            continue
        lang = lang_store.get_lang(user_id) or "ru"
        try:
            await bot.send_message(
                user_id,
                texts.t(lang, f"remind_{stage}"),
                reply_markup=open_app_kb(lang),
            )
        except TelegramForbiddenError:
            await db.mark_blocked(user_id)
        except TelegramRetryAfter as e:
            logging.warning("Flood control, sleep %s", e.retry_after)
            await asyncio.sleep(e.retry_after + 1)
            continue
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                await db.mark_blocked(user_id)
            else:
                logging.warning("Reminder failed for %s: %s", user_id, e)
        except TelegramAPIError as e:
            logging.warning("Reminder failed for %s: %s", user_id, e)
        else:
            await db.set_remind_stage(user_id, stage, last_activity)
        await asyncio.sleep(SEND_PAUSE)


async def reminder_loop(bot: Bot, db: Database) -> None:
    while True:
        try:
            if not is_night():
                await process(bot, db)
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("Reminder loop error")
        await asyncio.sleep(CHECK_INTERVAL)