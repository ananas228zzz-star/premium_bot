import config

REWARDS_EN = {
    "Telegram Premium на 3 месяца": "Telegram Premium for 3 months",
    "Telegram Premium на 6 месяцев": "Telegram Premium for 6 months",
    "Telegram Premium на 1 год": "Telegram Premium for 1 year",
}

T = {
    "ru": {
        "start": "Вы зашли в бота где вы можете получить Telegram Premium за несложные задания:",
        "open": "Открыть",
        "progress": "Новый реферал! Прогресс: {p}/{r}",
        "completed": "Вы добавили {n} человек! Подпишитесь на канал и получите {reward}.\n{link}",
        "subscribe_btn": "Подписаться на канал",
        "channel_msg": "Нажмите кнопку ниже, чтобы подписаться на канал:",
        "gate_msg": "Подайте заявку на вступление в канал, чтобы пользоваться ботом:",
        "gate_btn": "Подать заявку",
        "remind_1": "👋 Вы заглядывали за Telegram Premium, но так и не взяли задание. Это быстро: берёте задание и делитесь ссылкой. Остальное покажет приложение.",
        "remind_2": "💎 Ваш Telegram Premium всё ещё ждёт. Достаточно пригласить друзей по своей ссылке, прогресс виден прямо в приложении.",
        "remind_3": "⏳ Последнее напоминание: не упустите бесплатный Telegram Premium. Загляните в приложение, это займёт минуту.",
    },
    "en": {
        "start": "Welcome! Here you can get Telegram Premium by completing simple tasks:",
        "open": "Open",
        "progress": "New referral! Progress: {p}/{r}",
        "completed": "You invited {n} people! Subscribe to the channel and get {reward}.\n{link}",
        "subscribe_btn": "Subscribe to channel",
        "channel_msg": "Tap the button below to subscribe to the channel:",
        "gate_msg": "Send a join request to the channel to use the bot:",
        "gate_btn": "Send request",
        "remind_1": "👋 You stopped by for Telegram Premium but haven't taken a task yet. It's quick: take a task and share your link. The app shows the rest.",
        "remind_2": "💎 Your Telegram Premium is still waiting. Just invite friends with your link, the progress is right in the app.",
        "remind_3": "⏳ Last reminder: don't miss free Telegram Premium. Open the app, it takes a minute.",
    },
}


def t(lang: str, key: str, **kw) -> str:
    return T.get(lang, T["ru"])[key].format(**kw)


def reward(lang: str, value: str) -> str:
    if lang == "en":
        return REWARDS_EN.get(value, value)
    return value


def task_completed(lang: str, count: int, reward_name: str) -> str:
    return t(lang, "completed", n=count, reward=reward(lang, reward_name), link=config.CHANNEL_LINK)