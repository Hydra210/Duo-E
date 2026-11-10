from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


class ClearChannelView(discord.ui.View):
    def __init__(self, owner_id: int, channel: discord.TextChannel, database):
        super().__init__(timeout=60)
        self.owner_id = owner_id
        self.channel = channel
        self.database = database
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Only the person who started this action can confirm it.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Clear all messages", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="Confirmed. Clearing messages now…", view=self
        )
        self.stop()
        await interaction.followup.send(
            "The clear operation has started. Discord may take a while for channels with extensive history.",
            ephemeral=True,
        )
        try:
            deleted = await self.channel.purge(limit=None, bulk=True, reason=f"Requested by {interaction.user} ({interaction.user.id})")
            await self.database.add_audit_event(
                interaction.guild_id,
                interaction.user.id,
                "channel.clear",
                f"Cleared {len(deleted)} messages from channel {self.channel.id}",
                datetime.now(timezone.utc).isoformat(),
            )
            await interaction.followup.send(
                f"Finished. Deleted {len(deleted):,} messages from {self.channel.mention}.",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I don't have permission to manage messages in that channel.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            await interaction.followup.send(
                f"Discord stopped the operation: {exc}. Some messages may already have been deleted.",
                ephemeral=True,
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Clear cancelled.", view=self)
        self.stop()


class ChannelTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="channel_clear",
        description="Delete every message in the current text channel",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def channel_clear(self, interaction: discord.Interaction) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Run this command inside a regular text channel.", ephemeral=True
            )
            return
        if not interaction.guild.me.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "I need the Manage Messages permission in this channel.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        count = 0
        async for _message in channel.history(limit=None):
            count += 1

        if count == 0:
            await interaction.followup.send("This channel is already empty.", ephemeral=True)
            return

        view = ClearChannelView(interaction.user.id, channel, self.bot.database)
        await interaction.followup.send(
            f"This will permanently delete **all {count:,} messages** in {channel.mention}. "
            "This cannot be undone. Confirm to continue.",
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelTools(bot))
