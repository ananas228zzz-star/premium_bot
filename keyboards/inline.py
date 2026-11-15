from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

import config


def open_app_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть", web_app=WebAppInfo(url=config.WEBAPP_URL)
                )
            ]
        ]
    )