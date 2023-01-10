import aio_pika
import asyncio

from aio_pika import ExchangeType
from logging import Logger

from server.Utils import Utils


class AioRmqConsumer:

    def __init__(self, rmq_host: str,
                 rmq_port: int,
                 exchange_name: str,
                 queue_name: str,
                 logger: Logger,
                 exception_queue: asyncio.Queue):
        self._name = Utils.format_name('AIO_RMQ_Consumer')
        self._logger = logger
        self._exception_queue = exception_queue

        self._rmq_host = rmq_host
        self._rmq_port = rmq_port
        self._exchange_name = exchange_name
        self._queue_name = queue_name

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

        # todo put to queue ???

    async def _message_handler(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process():
            try:
                await self._process_message(message.body)
                await message.ack()
            except Exception as ex:
                await message.reject()
                await self._exception_queue.put((self.name, 'Error in Message', ex))

    async def _init_conn(self):
        # creating TCP connection to use RPC calls
        self._logger.info(f'{self.name} Connecting to RMQ: {self._rmq_host}:{self._rmq_port}')
        self._conn = await aio_pika.connect_robust(host=self._rmq_host, port=self._rmq_port)
        self._logger.info(f'{self.name} Connection Established: {self._rmq_host}:{self._rmq_port}')

    async def _init_channel(self):
        # create new channel inside TCP connection which is like separate erlang service
        self._logger.debug(f'{self.name} Openning Channel')
        self._channel = await self._conn.channel()
        self._logger.debug(f'{self.name} Channel Opened')

    async def _init_exchange(self):
        # inside channel we declare indempodent exchange
        self._logger.debug(f'{self.name} Declaring DIRECT exchange: {self._exchange_name}')
        self._exchange = await self._channel.declare_exchange(self._exchange_name, ExchangeType.DIRECT)
        self._logger.debug(f'{self.name} DIRECT exchange Declared: {self._exchange_name}')

    async def _init_queue(self):
        # also create idempodent queues
        self._logger.debug(f'{self.name} Declaring Queue: {self._queue_name}')
        self._queue = await self._channel.declare_queue(self._queue_name)
        self._logger.debug(f'{self.name} Queue Declared: {self._queue_name}')

    async def _init_bindings(self):
        # binding key
        binding_key = f'route_to_{self._exchange_name}'
        self._logger.debug(f'{self.name} Creating Binding Key: {binding_key}')
        await self._queue.bind(self._exchange, binding_key)
        self._logger.debug(f'{self.name} Binding Key Created: {binding_key}')

    async def _close_conn(self):
        # close TCP connection
        if self._conn:
            self._logger.info(f'{self.name} Closing Connection')
            await self._conn.close()
            self._logger.info(f'{self.name} Connection Closed')

    async def _connect(self) -> bool:
        try:
            await self._init_conn()
            await self._init_channel()
            await self._init_exchange()
            await self._init_queue()
            await self._init_bindings()

            await self._queue.consume(callback=self._message_handler, no_ack=self._no_ack)

            return True

        except asyncio.CancelledError:
            await self._close_conn()
            self._logger.warning(f'{self.name} Task Cancelled')
            return False

        except Exception as ex:
            await self._close_conn()
            await self._exception_queue.put((self.name, 'Error Consume', ex))
            return False

    async def consume(self):
        if not await self._connect():
            return

        try:
            await asyncio.Future()

        except asyncio.CancelledError as ex:
            await self._close_conn()
            self._logger.warning(f'{self.name} Task Cancelled!')

        except Exception as ex:
            await self._close_conn()
            await self._exception_queue.put((self.name, 'Running Consume', ex))
