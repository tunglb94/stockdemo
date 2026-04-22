import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class MarketConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer: client subscribe theo mã CK để nhận giá realtime."""

    async def connect(self):
        self.symbol = self.scope["url_route"]["kwargs"]["symbol"].upper()
        self.group_name = f"market_{self.symbol}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug(f"WS connected: {self.symbol}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def price_update(self, event):
        """Nhận event từ channel layer và đẩy xuống client."""
        await self.send(text_data=json.dumps({
            "type": "price_update",
            "symbol": self.symbol,
            "data": event["data"],
        }))
