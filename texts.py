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
