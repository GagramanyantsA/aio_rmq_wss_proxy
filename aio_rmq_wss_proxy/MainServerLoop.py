import asyncio

from logging import Logger

from . import AioRmqConsumer, AsyncServer, AsyncServerHandler, ClientsController, ClientsSender, Utils


class MainServerLoop:

    def __init__(self, name: str,
                 async_server: AsyncServer,
                 async_server_handler: AsyncServerHandler,
                 aio_rmq_consumer: AioRmqConsumer,
                 clients_controller: ClientsController,
                 clients_sender: ClientsSender,
                 logger: Logger,
                 exception_queue: asyncio.Queue):
        self._name: str = Utils.format_name(name)

        self._logger: Logger = logger
        self._exception_queue: asyncio.Queue = exception_queue

        self._async_server: AsyncServer = async_server
        self._async_server_handler: AsyncServer = async_server_handler
        self._aio_rmq_consumer: AioRmqConsumer = aio_rmq_consumer
        self._clients_controller: ClientsController = clients_controller
        self._clients_sender: ClientsSender = clients_sender

        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        self._main_task: asyncio.Task = self._loop.create_task(self.main(), name='Main-Task')

        self._tasks = [
            self._loop.create_task(self._async_server.run(), name='Async-Server-Task'),
            self._loop.create_task(self._clients_controller.check_clients(), name='Check-Clients-Task'),
            self._loop.create_task(self._aio_rmq_consumer.consume(), name='Transport-Consume-Task'),
            self._loop.create_task(self._clients_sender.queue_handler(), name='Clients-Sender-Task'),
            self._loop.create_task(self.exception_analysis(), name='Exc-Analysis-Task')
        ]

    @property
    def name(self) -> str:
        return self._name

    def run(self):
        self._loop.run_until_complete(self._main_task)

    def stop(self):
        self._loop.close()

    def cancel(self):
        self._main_task.cancel()

    async def exception_analysis(self):
        exc_analysis_name = Utils.format_name('Exception Analysis')

        self._logger.warning(f'{exc_analysis_name} Started')

        try:
            module_name, title, ex = await self._exception_queue.get()
            self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
            self._logger.exception(ex)
            self._exception_queue.task_done()

            await asyncio.sleep(2)

            while not self._exception_queue.empty():
                module_name, title, ex = await self._exception_queue.get()
                self._logger.critical(f'{module_name} | {title} | Exception: {ex}')
                self._logger.exception(ex)
                self._exception_queue.task_done()

            self.cancel()

        except asyncio.CancelledError:
            self._logger.warning(f'{exc_analysis_name} Cancelled')

        finally:
            self._logger.warning(f'{exc_analysis_name} Stopped')

    async def _cancel_tasks(self):
        self._async_server.stop()

        for task in self._tasks:
            if not task.done():
                task.cancel()
                await task

    async def main(self):
        self._logger.warning(f'{self.name} Started')

        try:
            await asyncio.wait(self._tasks)

        except asyncio.CancelledError:
            self._logger.warning(f'{self.name} Cancelled')
            await self._cancel_tasks()

        finally:
            self._logger.warning(f'{self.name} Stopped')
