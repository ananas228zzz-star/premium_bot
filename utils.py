import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
import lang_store
import texts


async def build_ref_link(bot: Bot, user_id: int) -> str:
    me = await bot.me()
    return f"https://t.me/{me.username}?start=ref_{user_id}"


def parse_referrer(args: Optional[str]) -> Optional[int]:
    if args and args.startswith("ref_") and args[4:].isdigit():
        return int(args[4:])
    return None


async def answer_with_photo(
    message: Message,
    image_name: str,
    caption: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> Message:
    path = config.IMAGES_DIR / image_name
    if path.is_file():
        return await message.answer_photo(
            FSInputFile(path), caption=caption, reply_markup=reply_markup
        )
    return await message.answer(caption, reply_markup=reply_markup)


async def notify_progress(bot: Bot, user_id: int, updates: list[dict]) -> None:
    lang = lang_store.get_lang(user_id) or "ru"
    for update in updates:
        markup = None
        if update["completed"]:
            text = texts.task_completed(lang, update["required"], update["reward"])
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=texts.t(lang, "subscribe_btn"), url=config.CHANNEL_LINK
                        )
                    ]
                ]
            )
        else:
            text = texts.t(lang, "progress", p=update["progress"], r=update["required"])
        try:
            await bot.send_message(
                user_id, text, reply_markup=markup, disable_web_page_preview=True
            )
        except TelegramAPIError:
            logging.warning("Не удалось отправить уведомление пользователю %s", user_id)
