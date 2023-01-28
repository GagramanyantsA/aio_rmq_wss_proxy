import asyncio
import json

from logging import Logger
from typing import Dict, List, Tuple

from . import Utils, ClientsController
from .SecuredWebsocketServerProtocol import SecuredWebsocketServerProtocol

from websockets.exceptions import ConnectionClosedOK as WS_ConnectionClosedOK, \
    ConnectionClosedError as WS_ConnectionClosedError


class ClientsSender:

    def __init__(self,
                 name: str,
                 from_queue: asyncio.Queue,
                 clients_controller: ClientsController,
                 logger: Logger,
                 exception_queue: asyncio.Queue):
        self._name = Utils.format_name(name)

        self._from_queue = from_queue
        self._clients_controller = clients_controller

        self._logger = logger
        self._exception_queue = exception_queue

    @property
    def name(self):
        return self._name

    def _remove_disconnected_client(self, client_id: str):
        self._clients_controller.remove_client(client_id)
        clients_amount = self._clients_controller.get_clients_amount()

        self._logger.debug(f'{self.name} Client Disconnected [Uuid: {client_id}][Clients Amount: {clients_amount}]')

    async def _send_update(self, receivers: List[Tuple[str, SecuredWebsocketServerProtocol]], message: Dict):
        if not len(receivers):
            return

        message = json.dumps(message)

        for receiver_data in receivers:
            client_id, receiver = receiver_data

            try:
                await receiver.send(message)
                self._logger.debug(f'{self.name} S > {message}')

            except WS_ConnectionClosedOK as ex:
                self._logger.debug(f'{self.name} Client [Id:{client_id}] Disconnected! Reason: {str(ex)}')
                self._remove_disconnected_client(client_id)

            except WS_ConnectionClosedError as ex:
                self._logger.debug(f'{self.name} Client [Id:{client_id}] Disconnected! Reason: {str(ex)}')
                self._remove_disconnected_client(client_id)

    async def _process_received_message(self, message_json: Dict):
        """
        This method is for describing how do we prepare received message from RMQ
        and send it to connected websocket clients
        :param message_json: message from RMQ
        :return: nothing (need just to send update)
        """
        raise NotImplementedError()

    async def queue_handler(self):
        self._logger.warning(f'{self.name} Started')

        try:
            while True:
                message_json = await self._from_queue.get()

                if not self._clients_controller.check_clients_exist():
                    self._from_queue.task_done()
                    continue

                await self._process_received_message(message_json)

                self._from_queue.task_done()

        except asyncio.CancelledError:
            self._logger.warning(f'{self.name} Stopped')
            return

        except Exception as ex:
            self._logger.error(f'{self.name} Stopped because of an Error')
            await self._exception_queue.put((self.name, 'Queue Handler', ex))
            return
