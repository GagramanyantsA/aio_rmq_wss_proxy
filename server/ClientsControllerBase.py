from typing import List, Tuple

from .SecuredWebsocketServerProtocol import SecuredWebsocketServerProtocol


class ClientsControllerBase:

    def __init__(self):
        self._clients = {}
        self._rooms = {}

    def get_receivers(self, room: str) -> List[Tuple[str, SecuredWebsocketServerProtocol]]:
        clients_ids = self._rooms[room]

        receivers = []

        for client_id in clients_ids:
            receivers.append((client_id, self._clients[client_id]))

        return receivers

    def check_clients_exist(self) -> bool:
        return len(self._clients) > 0

    def get_clients_amount(self) -> int:
        return len(self._clients)

    def clean_disconnected_clients(self) -> List[str]:
        lost_clients_ids = []

        for client_id in self._clients:
            if self._clients[client_id].closed:
                lost_clients_ids.append(client_id)

        for client_id in lost_clients_ids:
            self._clients.pop(client_id)

            for room_key in self._rooms:
                room = self._rooms[room_key]
                if client_id in room:
                    room.remove(client_id)

        return lost_clients_ids

    def add_new_client(self, client_id: str, websocket: SecuredWebsocketServerProtocol):
        self._clients[client_id] = websocket

    def remove_client(self, client_id: str):
        if client_id in self._clients:
            self._clients.pop(client_id)

        for room_key in self._rooms:
            room = self._rooms[room_key]
            if client_id in room:
                room.remove(client_id)

    def check_room_exist(self, room_name: str) -> bool:
        return room_name in self._rooms

    def subscribe_room(self, client_id: str, room_name: str):
        if client_id not in self._rooms[room_name]:
            self._rooms[room_name].append(client_id)

    def unsubscribe_room(self, client_id: str, room_name: str):
        if client_id in self._rooms[room_name]:
            self._rooms[room_name].remove(client_id)
