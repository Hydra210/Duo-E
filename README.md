# Duo-E

A modular Discord server management bot focused on backups, recovery, diagnostics, and controlled administration.

## Status

Early development. The current foundation includes:
- Discord slash-command bot with per-guild configuration
- SQLite persistence for backup metadata and scheduled tasks
- Cloudflare R2-compatible object storage
- Guild backup creation and listing
- Permission-gated destructive actions with confirmation prompts
- Structured logging and audit events

Restore, selective restore, templates, scheduled execution, dashboard, diagnostics, and automated recovery are planned modules and are not yet implemented.

## Requirements

- Python 3.11+
- A Discord bot application with the Server Members Intent enabled if member-related features are added
- Cloudflare R2 bucket and API credentials

## Setup

1. Create a virtual environment: `python -m venv .venv`
2. Activate it and install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in the values.
4. Invite the bot with `bot` and `applications.commands` scopes and only the permissions it needs.
5. Start it: `python -m duo_e`

Never commit your `.env` file or expose bot/R2 credentials.

## Configuration

See `.env.example`. Use a dedicated R2 bucket and credentials restricted to that bucket.

## Development

Run checks with:

```bash
python -m compileall duo_e
```

Duo-E is designed to fail closed: commands check permissions, destructive actions require confirmation, and operations are logged.
