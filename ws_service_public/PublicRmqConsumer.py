import asyncio
import json

from logging import Logger
from typing import Dict

from server import AioRmqConsumer


class PublicRmqConsumer(AioRmqConsumer):
    """

    Here we just need to override _process_message method and write how do you parse received message

    """

    def __init__(self, rmq_host: str, rmq_port: int, logger: Logger, exception_queue: asyncio.Queue):
        exchange_name = 'WS_EXCHANGE'
        queue_name = 'PUBLIC_WEBSOCKET_QUEUE'
        super(PublicRmqConsumer, self).__init__(rmq_host, rmq_port, exchange_name, queue_name, logger, exception_queue)

    def _check_message_data(self, data: Dict):
        pass

    async def _process_message(self, body: bytes):
        await super(PublicRmqConsumer, self)._process_message(body)

        message_data = json.loads(body)

        self._check_message_data(message_data)

        # todo put to queue ???
