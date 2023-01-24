import os

from logger import LoggerLoader
from _testing.public_sample.PublicWebsocketService import PublicWebsocketService

if __name__ == '__main__':
    logger = LoggerLoader('public_websocket_service.log', 'DEBUG', os.getcwd()).get_logger()

    http_host = 'localhost'
    http_port = 9001

    rmq_host = 'localhost'
    rmq_port = 5672

    server_loop = PublicWebsocketService(rmq_host, rmq_port, http_host, http_port, logger)

    try:
        server_loop.run()
    except KeyboardInterrupt:
        server_loop.cancel()
        server_loop.run()
    finally:
        server_loop.stop()
