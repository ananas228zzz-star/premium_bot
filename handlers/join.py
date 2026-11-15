import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ChatJoinRequest, Message

import gate_store
from database import Database

router = Router()


@router.chat_join_request()
async def on_join_request(event: ChatJoinRequest, db: Database):
    gate_id = gate_store.get_gate_id()
    logging.warning(
        "JOIN REQUEST: user=%s chat=%s gate=%s", event.from_user.id, event.chat.id, gate_id
    )
    if gate_id is not None and event.chat.id == gate_id:
        await db.add_join_request(event.from_user.id)


@router.channel_post(F.text == "/gate")
async def on_gate_command(message: Message):
    gate_store.set_gate_id(message.chat.id)
    logging.warning("GATE SET: %s", message.chat.id)
    try:
        await message.delete()
    except TelegramAPIError:
        pass