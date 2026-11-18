from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

import config
import texts


def open_app_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.t(lang, "open"), web_app=WebAppInfo(url=config.WEBAPP_URL)
                )
            ]
        ]
    )
