import logging

import httpx

LOGGER = logging.getLogger(__name__)


class DiscordAlerter:
    def __init__(self, webhook_url: str | None) -> None:
        self.webhook_url = webhook_url

    async def send(self, message: str) -> None:
        if not self.webhook_url:
            LOGGER.info("discord_alert_skipped", extra={"message": message})
            return
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.webhook_url, json={"content": message})
            response.raise_for_status()
