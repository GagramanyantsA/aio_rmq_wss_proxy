import asyncio

from logging import Logger
from typing import Dict

from aio_rmq_wss_proxy.AioRmqConsumer import AioRmqConsumer


class PublicRmqConsumer(AioRmqConsumer):
    """

    Here we need just to specify how do we check received message from RMQ

    """

    def __init__(self, rmq_host: str,
                 rmq_port: int,
                 received_messages_queue: asyncio.Queue,
                 logger: Logger,
                 exception_queue: asyncio.Queue):
        super(PublicRmqConsumer, self).__init__(rmq_host, rmq_port, 'WS_EXCHANGE', 'PUBLIC_WEBSOCKET_QUEUE',
                                                received_messages_queue, logger, exception_queue)

    def _check_message(self, message_json: Dict) -> str:
        # todo some logic to check message
        return ''
