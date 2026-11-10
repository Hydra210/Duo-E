from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import discord

from duo_e.database import Database
from duo_e.storage import R2Storage


def _overwrite_data(overwrites: dict) -> list[dict[str, Any]]:
    result = []
    for target, overwrite in overwrites.items():
        result.append({
            "target_type": "role" if isinstance(target, discord.Role) else "member",
            "target_id": target.id,
            "allow": overwrite.pair()[0].value,
            "deny": overwrite.pair()[1].value,
        })
    return result


def serialize_guild(guild: discord.Guild) -> dict[str, Any]:
    roles = [
        {
            "id": role.id,
            "name": role.name,
            "colour": role.colour.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
            "permissions": role.permissions.value,
            "position": role.position,
        }
        for role in sorted(guild.roles, key=lambda item: item.position)
        if not role.is_default() and not role.managed
    ]
    categories = []
    channels = []
    for channel in guild.channels:
        common = {
            "id": channel.id,
            "name": channel.name,
            "position": channel.position,
            "category_id": channel.category_id,
            "overwrites": _overwrite_data(channel.overwrites),
        }
        if isinstance(channel, discord.CategoryChannel):
            categories.append(common)
        elif isinstance(channel, discord.TextChannel):
            channels.append({
                **common,
                "type": "text",
                "topic": channel.topic,
                "nsfw": channel.nsfw,
                "slowmode_delay": channel.slowmode_delay,
                "default_auto_archive_duration": channel.default_auto_archive_duration,
            })
        elif isinstance(channel, discord.VoiceChannel):
            channels.append({
                **common,
                "type": "voice",
                "bitrate": channel.bitrate,
                "user_limit": channel.user_limit,
            })
        elif isinstance(channel, discord.StageChannel):
            channels.append({**common, "type": "stage"})
        elif isinstance(channel, discord.ForumChannel):
            channels.append({
                **common,
                "type": "forum",
                "topic": channel.topic,
                "nsfw": channel.nsfw,
                "slowmode_delay": channel.slowmode_delay,
            })

    return {
        "schema_version": 1,
        "guild": {"id": guild.id, "name": guild.name},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roles": roles,
        "categories": categories,
        "channels": channels,
    }


async def create_backup(
    guild: discord.Guild,
    actor_id: int,
    storage: R2Storage,
    database: Database,
) -> tuple[str, int]:
    backup_id = uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()
    object_key = f"guilds/{guild.id}/backups/{backup_id}.json"
    payload = serialize_guild(guild)
    size = await storage.put_json(object_key, payload)
    await database.add_backup((
        backup_id, guild.id, guild.name, object_key, created_at, actor_id, size
    ))
    await database.add_audit_event(
        guild.id, actor_id, "backup.create",
        f"Created backup {backup_id} ({size} bytes)", created_at
    )
    return backup_id, size
