import asyncio
from pathlib import Path
from typing import Optional

import aiosqlite

TASK_IN_PROGRESS = "in_progress"
TASK_COMPLETED = "completed"
REF_PENDING = "pending"
REF_COUNTED = "counted"

TASKS = [
    ("Добавить 10 человек", "Telegram Premium на 3 месяца", 10),
    ("Добавить 20 человек", "Telegram Premium на 6 месяцев", 20),
    ("Добавить 30 человек", "Telegram Premium на 1 год", 30),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    referrer_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    reward TEXT NOT NULL,
    required_referrals INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS user_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    UNIQUE (user_id, task_id)
);

CREATE TABLE IF NOT EXISTS referrals (
    referred_id INTEGER PRIMARY KEY,
    referrer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS join_requests (
    user_id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals (referrer_id, status);
CREATE INDEX IF NOT EXISTS idx_user_tasks_user ON user_tasks (user_id, status);
"""


class Database:
    def __init__(self, path: Path):
        self._path = path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._seed_tasks()
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    async def _seed_tasks(self) -> None:
        cursor = await self._conn.execute(
            "SELECT title, reward, required_referrals FROM tasks ORDER BY id"
        )
        current = [tuple(row) for row in await cursor.fetchall()]
        if current == TASKS:
            return
        await self._conn.execute("DELETE FROM user_tasks")
        await self._conn.execute("DELETE FROM tasks")
        await self._conn.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
        await self._conn.executemany(
            "INSERT INTO tasks (title, reward, required_referrals) VALUES (?, ?, ?)",
            TASKS,
        )
        await self._conn.execute("UPDATE referrals SET status = ?", (REF_PENDING,))

    async def add_join_request(self, user_id: int) -> None:
        async with self._lock:
            await self._conn.execute(
                "INSERT OR IGNORE INTO join_requests (user_id) VALUES (?)", (user_id,)
            )
            await self._conn.commit()

    async def has_join_request(self, user_id: int) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM join_requests WHERE user_id = ?", (user_id,)
        )
        return await cursor.fetchone() is not None

    async def register_user(
        self, user_id: int, username: Optional[str], referrer_id: Optional[int] = None
    ) -> tuple[bool, Optional[int]]:
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
            )
            if await cursor.fetchone():
                await self._conn.execute(
                    "UPDATE users SET username = ? WHERE user_id = ?", (username, user_id)
                )
                await self._conn.commit()
                return False, None

            valid_referrer = None
            if referrer_id and referrer_id != user_id:
                cursor = await self._conn.execute(
                    "SELECT 1 FROM users WHERE user_id = ?", (referrer_id,)
                )
                if await cursor.fetchone():
                    valid_referrer = referrer_id

            await self._conn.execute(
                "INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
                (user_id, username, valid_referrer),
            )
            if valid_referrer:
                await self._conn.execute(
                    "INSERT OR IGNORE INTO referrals (referred_id, referrer_id, status) "
                    "VALUES (?, ?, ?)",
                    (user_id, valid_referrer, REF_PENDING),
                )
            await self._conn.commit()
            return True, valid_referrer

    async def get_task(self, task_id: int) -> Optional[aiosqlite.Row]:
        cursor = await self._conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return await cursor.fetchone()

    async def get_available_tasks(self, user_id: int) -> list[aiosqlite.Row]:
        cursor = await self._conn.execute(
            """
            SELECT t.* FROM tasks t
            WHERE NOT EXISTS (
                SELECT 1 FROM user_tasks ut
                WHERE ut.task_id = t.id AND ut.user_id = ?
            )
            ORDER BY t.id
            """,
            (user_id,),
        )
        return await cursor.fetchall()

    async def get_active_tasks(self, user_id: int) -> list[aiosqlite.Row]:
        cursor = await self._conn.execute(
            """
            SELECT t.id, t.title, t.reward, t.required_referrals, ut.progress
            FROM user_tasks ut
            JOIN tasks t ON t.id = ut.task_id
            WHERE ut.user_id = ? AND ut.status = ?
            ORDER BY ut.id
            """,
            (user_id, TASK_IN_PROGRESS),
        )
        return await cursor.fetchall()

    async def take_task(
        self, user_id: int, task_id: int
    ) -> tuple[str, Optional[list[dict]]]:
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT 1 FROM user_tasks WHERE user_id = ? AND task_id = ?",
                (user_id, task_id),
            )
            if await cursor.fetchone():
                return "taken", None

            cursor = await self._conn.execute(
                "SELECT 1 FROM user_tasks WHERE user_id = ? AND status = ?",
                (user_id, TASK_IN_PROGRESS),
            )
            if await cursor.fetchone():
                return "busy", None

            await self._conn.execute(
                "INSERT INTO user_tasks (user_id, task_id, status) VALUES (?, ?, ?)",
                (user_id, task_id, TASK_IN_PROGRESS),
            )
            updates = await self._sync_progress(user_id)
            return "ok", updates

    async def sync_progress(self, user_id: int) -> list[dict]:
        async with self._lock:
            return await self._sync_progress(user_id)

    async def _sync_progress(self, user_id: int) -> list[dict]:
        updates = []
        cursor = await self._conn.execute(
            """
            SELECT ut.id, ut.progress, t.title, t.reward, t.required_referrals
            FROM user_tasks ut
            JOIN tasks t ON t.id = ut.task_id
            WHERE ut.user_id = ? AND ut.status = ?
            ORDER BY ut.id
            """,
            (user_id, TASK_IN_PROGRESS),
        )
        rows = await cursor.fetchall()

        for row in rows:
            required = row["required_referrals"]
            needed = required - row["progress"]
            cursor = await self._conn.execute(
                "SELECT referred_id FROM referrals "
                "WHERE referrer_id = ? AND status = ? "
                "ORDER BY created_at, referred_id LIMIT ?",
                (user_id, REF_PENDING, needed),
            )
            ids = [r["referred_id"] for r in await cursor.fetchall()]
            if not ids:
                continue

            placeholders = ",".join("?" * len(ids))
            await self._conn.execute(
                f"UPDATE referrals SET status = ? WHERE referred_id IN ({placeholders})",
                (REF_COUNTED, *ids),
            )

            progress = row["progress"] + len(ids)
            completed = progress >= required
            if completed:
                await self._conn.execute(
                    "UPDATE user_tasks SET progress = ?, status = ?, "
                    "completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (progress, TASK_COMPLETED, row["id"]),
                )
            else:
                await self._conn.execute(
                    "UPDATE user_tasks SET progress = ? WHERE id = ?",
                    (progress, row["id"]),
                )
            updates.append(
                {
                    "title": row["title"],
                    "reward": row["reward"],
                    "progress": progress,
                    "required": required,
                    "completed": completed,
                }
            )

        await self._conn.commit()
        return updates

    async def get_overview(self, user_id: int) -> list[aiosqlite.Row]:
        cursor = await self._conn.execute(
            """
            SELECT t.id, t.title, t.reward, t.required_referrals,
                   ut.status, ut.progress
            FROM tasks t
            LEFT JOIN user_tasks ut ON ut.task_id = t.id AND ut.user_id = ?
            ORDER BY t.id
            """,
            (user_id,),
        )
        return await cursor.fetchall()
