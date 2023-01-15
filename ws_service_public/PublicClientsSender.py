import asyncio

from logging import Logger
from typing import Dict, Optional

from server import ClientsSender
from ws_service_public.PublicClientsController import PublicClientsController
from ws_service_public.const import MessageKeys, Actions, Events


class PublicClientsSender(ClientsSender):
    """

    Here we need to specify how do we prepare update to our connected clients from queue message

    """

    def __init__(self, from_queue: asyncio.Queue,
                 clients_controller: PublicClientsController,
                 logger: Logger, exception_queue: asyncio.Queue):
        super(PublicClientsSender, self).__init__('Pub Clients Sender',
                                                  from_queue, clients_controller,
                                                  logger, exception_queue)

    def _prepare_update(self, message_json: Dict) -> Optional[Dict]:
        action = message_json[MessageKeys.ACTION]

        if action != Actions.TEST_UPDATE:
            self._logger.error(f'{self.name} Unsupported Action! {str(message_json)}')
            return None

        return {
            MessageKeys.EVENT: Events.DATA_UPDATE,
            MessageKeys.ROOM: 'public room 1',
            MessageKeys.RESULT: message_json[MessageKeys.DATA]
        }

    async def _process_received_message(self, message_json: Dict):
        message_to_send = self._prepare_update(message_json)

        if not message_to_send:
            return

        room = message_to_send[MessageKeys.ROOM]

        if not self._clients_controller.check_room_exist(message_to_send[room]):
            self._logger.warning(f'{self.name} RMQ unknown room {room}')
            return

        receivers = self._clients_controller.get_receivers(room)
        await self._send_update(receivers, message_to_send)
