import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    super_admin_id: int
    admin2_id: Optional[int] = None
    db_path: str = "bot.db"


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN env var is required")

    super_admin_raw = os.getenv("SUPER_ADMIN_ID", "").strip()
    if not super_admin_raw:
        raise RuntimeError("SUPER_ADMIN_ID env var is required")

    try:
        super_admin_id = int(super_admin_raw)
    except ValueError as exc:
        raise RuntimeError("SUPER_ADMIN_ID must be integer") from exc

    admin2_raw = os.getenv("ADMIN2_ID", "").strip()
    admin2_id: Optional[int] = None
    if admin2_raw:
        try:
            admin2_id = int(admin2_raw)
        except ValueError as exc:
            raise RuntimeError("ADMIN2_ID must be integer") from exc

    db_path = os.getenv("DB_PATH", "bot.db").strip() or "bot.db"
    return Config(
        bot_token=bot_token,
        super_admin_id=super_admin_id,
        admin2_id=admin2_id,
        db_path=db_path,
    )
