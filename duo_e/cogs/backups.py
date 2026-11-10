from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from duo_e.backup import create_backup
from duo_e.database import Database
from duo_e.storage import R2Storage


class Backups(commands.Cog):
    def __init__(self, bot: commands.Bot, database: Database, storage: R2Storage | None):
        self.bot = bot
        self.database = database
        self.storage = storage

    @app_commands.command(name="backup_create", description="Create a server structure backup")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def backup_create(self, interaction: discord.Interaction) -> None:
        if self.storage is None:
            await interaction.response.send_message(
                "Cloudflare R2 is not configured. Ask the bot owner to configure storage.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        backup_id, size = await create_backup(
            interaction.guild, interaction.user.id, self.storage, self.database
        )
        await interaction.followup.send(
            f"Backup created: `{backup_id}` · {size:,} bytes", ephemeral=True
        )

    @app_commands.command(name="backup_list", description="List this server's backups")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def backup_list(self, interaction: discord.Interaction) -> None:
        rows = await self.database.list_backups(interaction.guild_id)
        if not rows:
            await interaction.response.send_message("No backups found for this server.", ephemeral=True)
            return
        lines = [
            f"• `{backup_id}` — {created_at[:19]} UTC — {size:,} bytes"
            for backup_id, _name, created_at, _actor, size in rows[:20]
        ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="backup_delete", description="Delete one of this server's backups")
    @app_commands.describe(backup_id="ID shown by /backup_list")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def backup_delete(self, interaction: discord.Interaction, backup_id: str) -> None:
        if self.storage is None:
            await interaction.response.send_message("R2 storage is not configured.", ephemeral=True)
            return
        row = await self.database.get_backup(interaction.guild_id, backup_id)
        if row is None:
            await interaction.response.send_message("Backup not found in this server.", ephemeral=True)
            return

        view = ConfirmDeleteView(interaction.user.id)
        await interaction.response.send_message(
            f"Delete backup `{backup_id}` permanently?", view=view, ephemeral=True
        )
        await view.wait()
        if view.confirmed:
            await self.storage.delete(row[1])
            from datetime import datetime, timezone
            await self.database.add_audit_event(
                interaction.guild_id, interaction.user.id, "backup.delete",
                f"Deleted backup {backup_id}", datetime.now(timezone.utc).isoformat()
            )
            await interaction.followup.send("Backup deleted.", ephemeral=True)


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=30)
        self.owner_id = owner_id
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Only the person who started this action can confirm it.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Delete backup", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Deletion confirmed.", view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Deletion cancelled.", view=self)
        self.stop()


async def setup(bot: commands.Bot):
    await bot.add_cog(Backups(bot, bot.database, bot.storage))
