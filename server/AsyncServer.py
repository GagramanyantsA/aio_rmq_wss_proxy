import websockets

from logging import Logger

from .SecuredWebsocketServerProtocol import SecuredWebsocketServerProtocol


class AsyncServer:

    def __init__(self, ws_handler, host: str, port: int, logger: Logger):
        self._name = 'AsyncWSS'.ljust(15)

        self._logger = logger

        self._host = host
        self._port = port

        self._future_inst = websockets.serve(ws_handler=ws_handler,
                                             host=self._host,
                                             port=self._port,
                                             create_protocol=SecuredWebsocketServerProtocol)

        self._running_inst = None

    @property
    def name(self):
        return self._name

    async def run(self):
        self._running_inst = await self._future_inst
        self._logger.info(f'{self.name} Started [HOST: {self._host} PORT: {self._port}]')

    def stop(self):
        if self._running_inst:
            self._running_inst.close()
            self._logger.info(f'{self.name} Stopped')
        else:
            self._logger.warning(f'{self.name} Already Stopped')
