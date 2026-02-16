import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any, Concatenate, TypedDict

import jwt
import requests

from pathology_api.http import SessionManager


class ApimAuthenticationException(Exception):
    pass


# Type alias describing the expected signature for use with the `Authenticator.auth`
# decorator.
# Any function that takes a `requests.Session` as its first argument, followed by any
# number of additional arguments, and returns any type of value.
type AuthenticatedMethod[**P] = Callable[Concatenate[requests.Session, P], Any]


class ApimAuthenticator:
    class __AccessToken(TypedDict):
        value: str
        expiry: datetime

    def __init__(
        self,
        private_key: str,
        key_id: str,
        api_key: str,
        token_validity_threshold: timedelta,
        token_endpoint: str,
        session_manager: SessionManager,
    ):
        self._private_key = private_key
        self._key_id = key_id
        self._api_key = api_key
        self._token_validity_threshold = token_validity_threshold
        self._token_endpoint = token_endpoint
        self._session_manager = session_manager

        self.__access_token: ApimAuthenticator.__AccessToken | None = None

    def auth[**P](
        self, func: AuthenticatedMethod[P]
    ) -> Callable[[AuthenticatedMethod[P]], AuthenticatedMethod[P]]:
        """
        Decorate a given function with APIM authentication. This authentication will be
        provided via a `requests.Session` object.
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # If there isn't an access token yet, or the token will expire within the
            # token validity threshold, reauthenticate.
            if (
                self.__access_token is None
                or self.__access_token["expiry"] - datetime.now(tz=timezone.utc)
                < self._token_validity_threshold
            ):
                self.__access_token = self._authenticate()

            with self._session_manager.open_session() as session:
                session.headers.update(
                    {"Authorization": f"Bearer {self.__access_token['value']}"}
                )
                return func(session, *args, **kwargs)

        return wrapper

    def _create_client_assertion(self) -> str:
        claims = {
            "sub": self._api_key,
            "iss": self._api_key,
            "jti": str(uuid.uuid4()),
            "aud": self._token_endpoint,
            "exp": int(
                (datetime.now(tz=timezone.utc) + timedelta(seconds=30)).timestamp()
            ),
        }

        return jwt.encode(
            claims,
            self._private_key,
            algorithm="RS512",
            headers={"kid": self._key_id},
        )

    def _authenticate(self) -> __AccessToken:
        with self._session_manager.open_session() as session:
            response = session.post(
                self._token_endpoint,
                data={
                    "grant_type": "client_credentials",
                    "client_assertion_type": "urn:ietf:params:oauth"
                    ":client-assertion-type:jwt-bearer",
                    "client_assertion": self._create_client_assertion(),
                },
            )

            if response.status_code != 200:
                raise ApimAuthenticationException(
                    f"Failed to authenticate with APIM. "
                    f"Status code: {response.status_code}"
                    f", Response: {response.text}"
                )

            response_data = response.json()

            return {
                "value": response_data["access_token"],
                "expiry": datetime.now(tz=timezone.utc)
                + timedelta(seconds=response_data["expires_in"]),
            }
