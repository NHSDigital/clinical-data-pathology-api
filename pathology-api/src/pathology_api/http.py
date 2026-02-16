from datetime import timedelta
from typing import Any, TypedDict

import requests
from requests.adapters import HTTPAdapter


class ClientCertificate(TypedDict):
    certificate_path: str
    key_path: str


class SessionManager:
    class _Adapter(HTTPAdapter):
        """
        HTTPAdapter to apply default configuration to apply to all created
        `request.Session` objects.
        """

        def __init__(self, timeout: float):
            self._timeout = timeout
            super().__init__()

        def send(
            self,
            request: requests.PreparedRequest,
            *args: Any,
            **kwargs: Any,
        ) -> requests.Response:
            kwargs["timeout"] = self._timeout
            return super().send(request, *args, **kwargs)

    def __init__(
        self,
        client_timeout: timedelta,
        client_certificate: ClientCertificate | None = None,
    ):
        self._client_adapter = self._Adapter(timeout=client_timeout.total_seconds())
        self._client_certificate = client_certificate

    def open_session(self) -> requests.Session:
        session = requests.Session()

        if self._client_certificate is not None:
            session.cert = (
                self._client_certificate["certificate_path"],
                self._client_certificate["key_path"],
            )

        session.mount("https://", self._client_adapter)
        session.mount("http://", self._client_adapter)

        return session
