import config

START = "Вы зашли в бота где вы можете получить Telegram Premium за несложные задания:"


def referral_progress(progress: int, required: int) -> str:
    return f"Новый реферал! Прогресс: {progress}/{required}"


def task_completed(count: int, reward: str) -> str:
    return (
        f"Вы добавили {count} человек! "
        f"Подпишитесь на канал и получите {reward}.\n"
        f"{config.CHANNEL_LINK}"
    )