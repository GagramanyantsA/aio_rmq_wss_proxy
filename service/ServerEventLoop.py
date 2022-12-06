import asyncio

from logging import Logger

from server.AsyncServer import AsyncServer
from server.AsyncServerHandler import AsyncServerHandler
from server.ClientsControllerBase import ClientsControllerBase
from server.SecuredWebsocketServerProtocol import SecuredWebsocketServerProtocol


class ServerEventLoop:

    def __init__(self, host: str, port: int, logger: Logger):
        self._logger = logger
        self._exception_queue = asyncio.Queue()

        clients_controller = ClientsControllerBase()
        self._async_server_handler = AsyncServerHandler(clients_controller, self._logger, self._exception_queue)
        self._async_server = AsyncServer(self._async_server_handler.do_action, host, port, logger)

        self._running_server = None

    def setup(self):
        SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD = None
        SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD = None
        SecuredWebsocketServerProtocol.FORWARDING_IS_ON = False

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main())
        loop.close()

    def stop(self):
        self._async_server.stop()

    async def main(self):
        await self._async_server.run()

        module_name, title, ex = await self._exception_queue.get()
        self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
        self._logger.exception(ex)

        await asyncio.sleep(2)

        while not self._exception_queue.empty():
            module_name, title, ex = await self._exception_queue.get()
            self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
            self._logger.exception(ex)

        self._async_server.stop()


if __name__ == '__main__':
    import os
    from logger.LoggerLoader import LoggerLoader

    logger = LoggerLoader('ServerEventLoop.txt', 'DEBUG', os.getcwd()).get_logger()
    host = 'localhost'
    port = 9001

    server_loop = ServerEventLoop(host, port, logger)

    try:
        server_loop.run()
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        pass

    finally:
        server_loop.stop()
