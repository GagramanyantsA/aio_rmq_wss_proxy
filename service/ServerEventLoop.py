import asyncio
from concurrent.futures import FIRST_COMPLETED

from logging import Logger
from typing import Optional

from server.AioRmqConsumer import AioRmqConsumer
from server.AsyncServer import AsyncServer
from server.AsyncServerHandler import AsyncServerHandler
from server.ClientsControllerBase import ClientsControllerBase
from server.SecuredWebsocketServerProtocol import SecuredWebsocketServerProtocol
from server.Settings import Settings


class ServerEventLoop:

    def __init__(self, host: str, port: int, logger: Logger):
        self._name = Settings.format_name('Main Loop')

        self._logger = logger
        self._exception_queue = asyncio.Queue()

        self._clients_controller = ClientsControllerBase(self._logger, self._exception_queue)
        self._async_server_handler = AsyncServerHandler(self._clients_controller, self._logger, self._exception_queue)
        self._async_server = AsyncServer(self._async_server_handler.do_action, host, port, logger)

        self._received_messages_queue = asyncio.Queue()
        self._aio_rmq_consumer = AioRmqConsumer('localhost', 5672, 'websocket_exch', 'public_websocket',
                                                self._received_messages_queue, self._logger, self._exception_queue)

        self._runserver_task: Optional[asyncio.Task] = None
        self._check_clients_task: Optional[asyncio.Task] = None
        self._transport_consume_task: Optional[asyncio.Task] = None

    @property
    def name(self):
        return self._name

    def setup(self):
        SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD = None
        SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD = None
        SecuredWebsocketServerProtocol.FORWARDING_IS_ON = False

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main())
        loop.close()

    def stop(self):
        if self._runserver_task and not self._runserver_task.done():
            self._runserver_task.cancel()
            self._logger.info(f'{self.name} \'{self._async_server.name}\' Task cancelled!')

        self._async_server.stop()

        if self._check_clients_task and not self._check_clients_task.done():
            self._check_clients_task.cancel()
            self._logger.info(f'{self.name} \'{self._clients_controller.name}\' Task cancelled!')

        if self._transport_consume_task and not self._transport_consume_task.done():
            self._transport_consume_task.cancel()
            self._logger.info(f'{self.name} \'{self._aio_rmq_consumer.name}\' Task cancelled!')

    async def main(self):
        self._runserver_task = asyncio.create_task(self._async_server.run())
        self._check_clients_task = asyncio.create_task(self._clients_controller.check_clients())
        self._transport_consume_task = asyncio.create_task(self._aio_rmq_consumer.consume())

        await asyncio.wait([
            self._runserver_task,
            self._check_clients_task,
            self._transport_consume_task
        ], return_when=FIRST_COMPLETED)

        if not self._runserver_task.done():
            await self._runserver_task

        module_name, title, ex = await self._exception_queue.get()
        self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
        self._logger.exception(ex)

        await asyncio.sleep(2)

        while not self._exception_queue.empty():
            module_name, title, ex = await self._exception_queue.get()
            self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
            self._logger.exception(ex)

        self.stop()


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
