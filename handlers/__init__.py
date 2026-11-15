from aiogram import Router

from . import join, start


def setup_routers() -> Router:
    router = Router()
    router.include_routers(start.router, join.router)
    return router