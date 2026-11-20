import logging

from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

import lang_store
import texts
from database import Database
from keyboards.inline import open_app_kb
from utils import answer_with_photo, notify_progress, parse_referrer

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, db: Database, bot: Bot):
    user = message.from_user
    referrer_id = parse_referrer(command.args)
    is_new, valid_referrer = await db.register_user(user.id, user.username, referrer_id)
    await db.touch_activity(user.id, unblock=True)
    logging.warning(
        "START: user=%s args=%s ref=%s is_new=%s valid_ref=%s",
        user.id, command.args, referrer_id, is_new, valid_referrer,
    )
    lang = lang_store.resolve(user.id, user.language_code)

    await answer_with_photo(message, "start.jpg", texts.t(lang, "start"), open_app_kb(lang))

    if is_new and valid_referrer:
        updates = await db.sync_progress(valid_referrer)
        await notify_progress(bot, valid_referrer, updates)