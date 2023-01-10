import websockets

from logging import Logger

from .Settings import Settings


class AsyncServer:

    def __init__(self, ws_handler, websocket_protocol_class, host: str, port: int, logger: Logger):
        self._name = Settings.format_name('AsyncWSS')

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
        self._logger.info(f'{self.name} Started [HOST: {self._host} PORT: {self._port}]')

    def stop(self):
        if self._running_inst and self._running_inst.is_serving():
            self._running_inst.close()
            self._logger.info(f'{self.name} Stopped')
        else:
            self._logger.warning(f'{self.name} Already Stopped')
