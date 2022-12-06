import http

import urllib.parse as urllib

from typing import Optional

from websockets.datastructures import Headers
from websockets.legacy.server import HTTPResponse
from websockets.server import WebSocketServerProtocol


class SecuredWebsocketServerProtocol(WebSocketServerProtocol):
    CHECK_TOKEN_METHOD = None
    CHECK_IP_ADDRESS_METHOD = None
    FORWARDING_IS_ON = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.client_ip = None

    def get_auth_token(self, path: str, request_headers: Headers) -> Optional[str]:
        auth_token = request_headers.get("Authorization", None)

        if auth_token is not None:
            return auth_token

        parsed = urllib.urlparse(path)
        auth_token = urllib.parse_qs(parsed.query).get('authorization', None)

        return None if auth_token is None else auth_token[0]

    def get_ip_address(self, request_headers: Headers):
        if SecuredWebsocketServerProtocol.FORWARDING_IS_ON:
            ip_header = request_headers.get('X-Forwarded-For', None)
            return ip_header.split(',')[0] if ip_header else None

        else:
            return self.remote_address[0]

    async def process_request(self, path: str, request_headers: Headers) -> Optional[HTTPResponse]:
        self.client_ip = self.get_ip_address(request_headers)

        if self.client_ip is None:
            return http.HTTPStatus.BAD_REQUEST, [], b"Ip address header is missing\n"

        if SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD is not None:
            auth_token = self.get_auth_token(path, request_headers)

            if auth_token is None:
                return http.HTTPStatus.UNAUTHORIZED, [], b"Missing credentials\n"

            self.user_id = SecuredWebsocketServerProtocol.CHECK_TOKEN_METHOD(auth_token)

            if self.user_id is None:
                return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid credentials\n"

            if SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD is not None:
                success = SecuredWebsocketServerProtocol.CHECK_IP_ADDRESS_METHOD(auth_token, self.client_ip)

                if not success:
                    return http.HTTPStatus.UNAUTHORIZED, [], b'Current IP address is not allowed\n'

        return await super(SecuredWebsocketServerProtocol, self).process_request(path, request_headers)
