import aio_pika
import asyncio

from logging import Logger

from aio_pika import ExchangeType

from server.Settings import Settings


class AioRmqConsumer:

    def __init__(self, rmq_host: str,
                 rmq_port: int,
                 exchange_name: str,
                 queue_name: str,
                 out_queue: asyncio.Queue,
                 logger: Logger,
                 exception_queue: asyncio.Queue):
        self._name = Settings.format_name('AIO_RMQ_Consumer')
        self._logger = logger
        self._exception_queue = exception_queue

        self._rmq_host = rmq_host
        self._rmq_port = rmq_port
        self._exchange_name = exchange_name
        self._queue_name = queue_name

        self._out_queue = out_queue

        self._no_ack = False

        self._conn = None
        self._channel = None
        self._exchange = None
        self._queue = None

    @property
    def name(self) -> str:
        return self._name

    async def _process_message(self, body):
        self._logger.info(f'{self.name} R < {body}')

        # todo parsing
        # todo put to out queue
        pass

    async def _message_handler(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process():
            await self._process_message(message.body)

    async def consume(self):
        connection_attempts = 0
        while True:
            connection_attempts += 1

            try:
                # creating TCP connection to use RPC calls
                self._logger.info(f'{self.name} Connecting to RMQ: {self._rmq_host}:{self._rmq_port}')
                self._conn = await aio_pika.connect_robust(host=self._rmq_host, port=self._rmq_port)
                self._logger.info(f'{self.name} Connection Established: {self._rmq_host}:{self._rmq_port}')

                # create new channel inside TCP connection which is like separate erlang service
                self._logger.info(f'{self.name} Openning Channel')
                self._channel = await self._conn.channel()
                self._logger.info(f'{self.name} Channel Opened')

                # inside channel we declare indempodent exchange
                self._logger.info(f'{self.name} Declaring DIRECT exchange: {self._exchange_name}')
                self._exchange = await self._channel.declare_exchange(self._exchange_name, ExchangeType.DIRECT)
                self._logger.info(f'{self.name} Declared DIRECT exchange: {self._exchange_name}')

                # also create idempodent queues
                self._logger.info(f'{self.name} Declaring Queue: {self._queue_name}')
                self._queue = await self._channel.declare_queue(self._queue_name)
                self._logger.info(f'{self.name} Declared Queue: {self._queue_name}')

                # binding key
                binding_key = f'route_to_{self._exchange_name}'
                self._logger.info(f'{self.name} Creating Binding Key: {binding_key}')
                await self._queue.bind(self._exchange, binding_key)
                self._logger.info(f'{self.name} Created Binding Key: {binding_key}')

                await self._queue.consume(self._message_handler, self._no_ack)

            except Exception as ex:
                if connection_attempts <= 3:
                    self._logger.info(f'{self.name} Error Consuming: {ex}')

                    if self._channel:
                        self._logger.info(f'{self.name} Closing Channel')
                        await self._channel.close()
                        self._logger.info(f'{self.name} Closed Channel')

                    if self._conn:
                        self._logger.info(f'{self.name} Closing Connection')
                        await self._conn.close()
                        self._logger.info(f'{self.name} Closed Connection')

                    await asyncio.sleep(3)
                    continue

                else:
                    await self._exception_queue.put((self.name, 'Error Consume', ex))
                    return

            break

        try:
            await asyncio.Future()
        finally:
            self._logger.info(f'{self.name} Closing Channel')
            await self._channel.close()
            self._logger.info(f'{self.name} Closed Channel')

            self._logger.info(f'{self.name} Closing Connection')
            await self._conn.close()
            self._logger.info(f'{self.name} Closed Connection')
