import asyncio
from concurrent.futures import FIRST_COMPLETED

from logging import Logger

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
        self._async_server = AsyncServer(self._async_server_handler.do_action,
                                         SecuredWebsocketServerProtocol,
                                         host, port, logger)

        self._received_messages_queue = asyncio.Queue()
        self._aio_rmq_consumer = AioRmqConsumer('localhost', 5672, 'websocket_exch', 'public_websocket',
                                                self._received_messages_queue, self._logger, self._exception_queue)

        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        self._main_task: asyncio.Task = self._loop.create_task(self.main(),
                                                               name='Main-Task')
        self._runserver_task: asyncio.Task = self._loop.create_task(self._async_server.run(),
                                                                    name='Async-Server-Task')
        self._check_clients_task: asyncio.Task = self._loop.create_task(self._clients_controller.check_clients(),
                                                                        name='Check-Clients-Task')
        self._transport_consume_task: asyncio.Task = self._loop.create_task(self._aio_rmq_consumer.consume(),
                                                                            name='Transport-Consume-Task')

    @property
    def name(self):
        return self._name

    def setup(self):
        SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD = None
        SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD = None
        SecuredWebsocketServerProtocol.FORWARDING_IS_ON = False

    def run(self):
        self._loop.run_until_complete(self._main_task)

    def restart_to_cancel_tasks(self):
        def stop_loop():
            self._loop.stop()

        self._loop.call_later(1, stop_loop)
        self._loop.run_forever()

    def stop(self):
        self._loop.close()

    def cancel_all_tasks(self, with_main: bool = True):
        main_task_name = self._main_task.get_name()

        known_tasks = [
            main_task_name,
            self._runserver_task.get_name(),
            self._check_clients_task.get_name(),
            self._transport_consume_task.get_name(),
        ]

        for task in asyncio.all_tasks(self._loop):
            task_name = task.get_name()

            if not with_main and task_name == main_task_name:
                continue

            task.cancel()

            if task_name in known_tasks:
                self._logger.warning(f'{self.name} \'{task_name}\' Task Cancel Sent')

    async def main(self):
        await asyncio.wait([
            self._runserver_task,
            self._check_clients_task,
            self._transport_consume_task
        ], return_when=FIRST_COMPLETED)

        try:
            module_name, title, ex = await self._exception_queue.get()
            self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
            self._logger.exception(ex)

            await asyncio.sleep(2)

            while not self._exception_queue.empty():
                module_name, title, ex = await self._exception_queue.get()
                self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
                self._logger.exception(ex)

            self.cancel_all_tasks(with_main=False)

        except asyncio.CancelledError:
            self._logger.warning(f'{self.name} Main Task Cancelled!')


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
        server_loop.cancel_all_tasks(with_main=True)
        server_loop.restart_to_cancel_tasks()
    finally:
        server_loop.stop()
