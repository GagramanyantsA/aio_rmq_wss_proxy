import asyncio

from logging import Logger

from server import AsyncServer, MainServerLoop, SecuredWebsocketServerProtocol, AioRmqConsumer

from ws_service_public.PublicAsyncServerHandler import PublicAsyncServerHandler
from ws_service_public.PublicClientsController import PublicClientsController


class PublicWebsocketService(MainServerLoop):
    """

    Just need to describe our instances and that's all

    """

    def __init__(self, rmq_host: str, rmq_port: int,
                 ws_host: str, ws_port: int,
                 logger: Logger):
        exception_queue = asyncio.Queue()

        clients_controller = PublicClientsController(logger, exception_queue)

        async_server_handler = PublicAsyncServerHandler(clients_controller, logger, exception_queue)

        # setup for websocket instance which is like connected client
        SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD = None
        SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD = None
        SecuredWebsocketServerProtocol.FORWARDING_IS_ON = False

        async_server = AsyncServer(async_server_handler.do_action,
                                   SecuredWebsocketServerProtocol,
                                   ws_host, ws_port, logger)

        aio_rmq_consumer = AioRmqConsumer(rmq_host, rmq_port,
                                          'WS_EXCHANGE', 'PUBLIC_WEBSOCKET_QUEUE',
                                          logger, exception_queue)

        super(PublicWebsocketService, self).__init__('Public WS Service',
                                                     async_server,
                                                     async_server_handler,
                                                     aio_rmq_consumer,
                                                     clients_controller,
                                                     logger,
                                                     exception_queue)
