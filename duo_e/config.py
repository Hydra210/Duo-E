from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    discord_token: str
    dev_guild_id: int | None
    database_path: Path
    log_level: str
    r2_account_id: str | None
    r2_access_key_id: str | None
    r2_secret_access_key: str | None
    r2_bucket_name: str | None
    r2_endpoint_url: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise RuntimeError("DISCORD_TOKEN is required")

        guild_raw = os.getenv("DEV_GUILD_ID", "").strip()
        return cls(
            discord_token=token,
            dev_guild_id=int(guild_raw) if guild_raw else None,
            database_path=Path(os.getenv("DATABASE_PATH", "data/duo_e.sqlite3")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            r2_account_id=os.getenv("R2_ACCOUNT_ID"),
            r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            r2_bucket_name=os.getenv("R2_BUCKET_NAME"),
            r2_endpoint_url=os.getenv("R2_ENDPOINT_URL"),
        )

    @property
    def r2_configured(self) -> bool:
        return all((
            self.r2_account_id,
            self.r2_access_key_id,
            self.r2_secret_access_key,
            self.r2_bucket_name,
            self.r2_endpoint_url,
        ))
