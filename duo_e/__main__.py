from __future__ import annotations

import logging

import discord
from discord.ext import commands

from duo_e.config import Settings
from duo_e.database import Database
from duo_e.storage import R2Storage


class DuoEBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self.database = Database(settings.database_path)
        self.storage = R2Storage(settings) if settings.r2_configured else None

    async def setup_hook(self) -> None:
        await self.database.initialize()
        await self.load_extension("duo_e.cogs.backups")
        await self.load_extension("duo_e.cogs.channel_tools")
        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        logging.getLogger("duo_e").info("Logged in as %s (%s)", self.user, self.user.id)


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    DuoEBot(settings).run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
