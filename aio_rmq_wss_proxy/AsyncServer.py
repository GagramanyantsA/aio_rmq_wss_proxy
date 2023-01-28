import websockets

from logging import Logger
from typing import Type, Callable, Coroutine

from . import Utils

from websockets.server import WebSocketServerProtocol


class AsyncServer:

    def __init__(self, ws_handler: Callable[[WebSocketServerProtocol, str], Coroutine],
                 websocket_protocol_class: Type[WebSocketServerProtocol],
                 host: str,
                 port: int,
                 logger: Logger):
        self._name = Utils.format_name('AsyncWSS')

        self._logger = logger

        self._host = host
        self._port = port

        self._future_inst = websockets.serve(ws_handler=ws_handler,
                                             host=self._host,
                                             port=self._port,
                                             create_protocol=websocket_protocol_class)

        self._running_inst = None

    @property
    def name(self):
        return self._name

    async def run(self):
        self._running_inst = await self._future_inst
        self._logger.warning(f'{self.name} Started [HOST: {self._host} PORT: {self._port}]')

    def stop(self):
        if self._running_inst and self._running_inst.is_serving():
            self._running_inst.close()
            self._logger.warning(f'{self.name} Stopped')
        else:
            self._logger.warning(f'{self.name} Already Stopped')
