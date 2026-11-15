from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

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

    await answer_with_photo(message, "start.jpg", texts.START, open_app_kb())

    if is_new and valid_referrer:
        updates = await db.sync_progress(valid_referrer)
        await notify_progress(bot, valid_referrer, updates)