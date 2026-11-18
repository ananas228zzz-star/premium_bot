from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.web_app import safe_parse_webapp_init_data
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config
import gate_store
import lang_store
import texts
from database import Database
from utils import build_ref_link, notify_progress


class AuthBody(BaseModel):
    init_data: str


class TakeBody(AuthBody):
    task_id: int


class LangBody(AuthBody):
    lang: str


def create_app(db: Database, bot: Bot) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    def auth(init_data: str):
        try:
            data = safe_parse_webapp_init_data(config.BOT_TOKEN, init_data)
        except ValueError:
            raise HTTPException(status_code=401, detail="Откройте приложение через Telegram")
        if data.user is None:
            raise HTTPException(status_code=401, detail="Откройте приложение через Telegram")
        return data.user

    def user_lang(user) -> str:
        return lang_store.resolve(user.id, getattr(user, "language_code", None))

    async def gate_passed(user_id: int) -> bool:
        if not config.GATE_LINK:
            return True
        if await db.has_join_request(user_id):
            return True
        gate_id = gate_store.get_gate_id()
        if gate_id is not None:
            try:
                member = await bot.get_chat_member(gate_id, user_id)
            except TelegramAPIError:
                return False
            if member.status in ("member", "administrator", "creator"):
                await db.add_join_request(user_id)
                return True
        return False

    async def build_state(user) -> dict:
        await db.register_user(user.id, user.username, None)
        passed = await gate_passed(user.id)
        base = {
            "name": user.first_name,
            "lang": user_lang(user),
            "gate_required": bool(config.GATE_LINK),
            "gate_passed": passed,
            "gate_link": config.GATE_LINK,
            "support": config.SUPPORT_USERNAME,
        }
        if not passed:
            base.update(
                {
                    "ref_link": "",
                    "channel_link": "",
                    "can_check": False,
                    "tasks": [],
                }
            )
            return base
        rows = await db.get_overview(user.id)
        link = await build_ref_link(bot, user.id)
        base.update(
            {
                "ref_link": link,
                "channel_link": config.CHANNEL_LINK,
                "can_check": bool(config.CHANNEL_ID),
                "tasks": [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "reward": row["reward"],
                        "required": row["required_referrals"],
                        "status": row["status"] or "new",
                        "progress": row["progress"] or 0,
                    }
                    for row in rows
                ],
            }
        )
        return base

    async def send_link(user_id: int, link: str, text: str, button: str) -> None:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=button, url=link)]]
        )
        try:
            await bot.send_message(user_id, text, reply_markup=markup)
        except TelegramAPIError:
            raise HTTPException(status_code=502, detail="Не удалось отправить сообщение")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(
            config.WEBAPP_DIR / "index.html",
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/api/state")
    async def state(body: AuthBody):
        user = auth(body.init_data)
        return await build_state(user)

    @app.post("/api/set_lang")
    async def set_lang(body: LangBody):
        user = auth(body.init_data)
        if body.lang not in ("ru", "en"):
            raise HTTPException(status_code=400, detail="Bad language")
        lang_store.set_lang(user.id, body.lang)
        return {"ok": True}

    @app.post("/api/take")
    async def take(body: TakeBody):
        user = auth(body.init_data)
        await db.register_user(user.id, user.username, None)
        if not await gate_passed(user.id):
            raise HTTPException(status_code=403, detail="Сначала подайте заявку в канал")
        task = await db.get_task(body.task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Задание не найдено")
        status, updates = await db.take_task(user.id, body.task_id)
        if status == "busy":
            raise HTTPException(
                status_code=409, detail="Сначала выполните текущее задание"
            )
        if status == "taken":
            raise HTTPException(status_code=409, detail="Вы уже взяли это задание")
        await notify_progress(bot, user.id, updates)
        return await build_state(user)

    @app.post("/api/gate_pass")
    async def gate_pass(body: AuthBody):
        user = auth(body.init_data)
        await db.register_user(user.id, user.username, None)
        return {"ok": await gate_passed(user.id)}

    @app.post("/api/send_channel")
    async def send_channel(body: AuthBody):
        user = auth(body.init_data)
        if not config.CHANNEL_LINK:
            raise HTTPException(status_code=400, detail="Ссылка на канал не указана")
        lang = user_lang(user)
        await send_link(
            user.id,
            config.CHANNEL_LINK,
            texts.t(lang, "channel_msg"),
            texts.t(lang, "subscribe_btn"),
        )
        return {"ok": True}

    @app.post("/api/send_gate")
    async def send_gate(body: AuthBody):
        user = auth(body.init_data)
        if not config.GATE_LINK:
            raise HTTPException(status_code=400, detail="Ссылка не указана")
        lang = user_lang(user)
        await send_link(
            user.id,
            config.GATE_LINK,
            texts.t(lang, "gate_msg"),
            texts.t(lang, "gate_btn"),
        )
        return {"ok": True}

    @app.post("/api/check_sub")
    async def check_sub(body: AuthBody):
        user = auth(body.init_data)
        if not config.CHANNEL_ID:
            raise HTTPException(status_code=400, detail="Проверка подписки отключена")
        try:
            member = await bot.get_chat_member(int(config.CHANNEL_ID), user.id)
        except (TelegramAPIError, ValueError):
            raise HTTPException(
                status_code=502,
                detail="Не удалось проверить подписку. Бот должен быть админом канала",
            )
        return {"subscribed": member.status in ("member", "administrator", "creator")}

    return app
