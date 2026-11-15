import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.types import MenuButtonWebApp, WebAppInfo

import config
from api.app import create_app
from database import Database
from handlers import setup_routers


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not config.BOT_TOKEN:
        raise RuntimeError("Укажите BOT_TOKEN в файле .env")
    if not config.WEBAPP_URL.startswith("https://"):
        raise RuntimeError("Укажите WEBAPP_URL (https://...) в файле .env")

    db = Database(config.DB_PATH)
    await db.connect()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(db=db)
    dp.include_router(setup_routers())

    app = create_app(db, bot)
    server = uvicorn.Server(
        uvicorn.Config(app, host=config.HOST, port=config.PORT, log_level="info")
    )
    server_task = asyncio.create_task(server.serve())

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть", web_app=WebAppInfo(url=config.WEBAPP_URL)
            )
        )
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "channel_post", "chat_join_request"],
        )
    finally:
        server.should_exit = True
        await server_task
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())