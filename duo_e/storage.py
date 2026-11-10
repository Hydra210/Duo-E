from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3
from botocore.config import Config

from duo_e.config import Settings


class R2Storage:
    def __init__(self, settings: Settings):
        if not settings.r2_configured:
            raise RuntimeError("Cloudflare R2 is not configured")
        self.bucket = settings.r2_bucket_name
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    async def put_json(self, key: str, payload: dict[str, Any]) -> int:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        return len(body)

    async def get_json(self, key: str) -> dict[str, Any]:
        response = await asyncio.to_thread(
            self.client.get_object, Bucket=self.bucket, Key=key
        )
        raw = await asyncio.to_thread(response["Body"].read)
        return json.loads(raw)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(
            self.client.delete_object, Bucket=self.bucket, Key=key
        )
