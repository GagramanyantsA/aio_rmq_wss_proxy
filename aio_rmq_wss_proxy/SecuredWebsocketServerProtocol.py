import http

import urllib.parse as urllib

from typing import Optional

from websockets.datastructures import Headers
from websockets.legacy.server import HTTPResponse
from websockets.server import WebSocketServerProtocol


class SecuredWebsocketServerProtocol(WebSocketServerProtocol):
    CHECK_TOKEN_METHOD = None
    CHECK_IP_ADDRESS_METHOD = None
    CHECK_DEVICE_METHOD = None
    FORWARDING_IS_ON = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.client_ip = None

    def get_auth_token(self, path: str, request_headers: Headers) -> Optional[str]:
        auth_token = request_headers.get("Authorization", None)

        if auth_token:
            return auth_token

        parsed = urllib.urlparse(path)
        auth_token = urllib.parse_qs(parsed.query).get('authorization', None)

        return auth_token[0] if auth_token else None

    def get_device_identifier(self, request_headers: Headers):
        return request_headers.get('Device-Identifier', None)

    def get_ip_address(self, request_headers: Headers):
        if SecuredWebsocketServerProtocol.FORWARDING_IS_ON:
            ip_header = request_headers.get('X-Forwarded-For', None)
            return ip_header.split(',')[0] if ip_header else None

        else:
            return self.remote_address[0]

    async def process_request(self, path: str, request_headers: Headers) -> Optional[HTTPResponse]:
        self.client_ip = self.get_ip_address(request_headers)

        if not self.client_ip:
            return http.HTTPStatus.BAD_REQUEST, [], b"Ip address header is missing\n"

        if SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD:
            auth_token = self.get_auth_token(path, request_headers)

            if not auth_token:
                return http.HTTPStatus.UNAUTHORIZED, [], b"Missing credentials\n"

            self.user_id = SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD(auth_token)

            if not self.user_id:
                return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid credentials\n"

            if SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD:
                success = SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD(auth_token, self.client_ip)

                if not success:
                    return http.HTTPStatus.UNAUTHORIZED, [], b'Current IP address is not allowed\n'

            if SecuredWebsocketServerProtocol.CHECK_DEVICE_METHOD:
                device_identifier = self.get_device_identifier(request_headers)

                if not device_identifier:
                    return http.HTTPStatus.UNAUTHORIZED, [], b'Missing device identifier\n'

                success = SecuredWebsocketServerProtocol.CHECK_DEVICE_METHOD(auth_token, device_identifier)

                if not success:
                    return http.HTTPStatus.UNAUTHORIZED, [], b'Current device identifier is not allowed\n'

        return await super(SecuredWebsocketServerProtocol, self).process_request(path, request_headers)
