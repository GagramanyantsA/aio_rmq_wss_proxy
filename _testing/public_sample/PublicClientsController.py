import asyncio

from logging import Logger

from server import ClientsControllerBase


class PublicClientsController(ClientsControllerBase):
    """

    Here we just need to specify the rooms which are supported by our server

    """

    def __init__(self, logger: Logger, exception_queue: asyncio.Queue):
        super(PublicClientsController, self).__init__(logger, exception_queue)

        for room_num in range(1, 5):
            self._rooms[f'public room {room_num}'] = []
