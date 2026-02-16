"""Pytest configuration and shared fixtures for pathology API tests."""

import os
from datetime import timedelta
from typing import Literal, Protocol, cast

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

_RequestMethod = Literal["GET", "POST"]


class Client(Protocol):
    """Protocol defining the interface for HTTP clients."""

    def send(
        self, data: str, path: str, request_method: _RequestMethod
    ) -> requests.Response:
        """
        Send a request to the APIs with some given parameters.
        Args:
            data: The data to send in the request payload
            path: The path to send the request to
            request_method: The HTTP method to use for the request
        Returns:
            Response object from the request
        """
        ...

    def send_without_payload(
        self, path: str, request_method: _RequestMethod
    ) -> requests.Response:
        """
        Send a request to the APIs without a payload.
        Args:
            path: The path to send the request to
            request_method: The HTTP method to use for the request
        Returns:
            Response object from the request
        """
        ...


class LocalClient:
    """A simple HTTP client for testing purposes."""

    def __init__(self, lambda_url: str, timeout: timedelta = timedelta(seconds=1)):
        self._lambda_url = lambda_url
        self._timeout = timeout.total_seconds()

    def send(
        self, data: str, path: str, request_method: _RequestMethod
    ) -> requests.Response:

        return self._send(
            data=data, path=path, include_payload=True, request_method=request_method
        )

    def send_without_payload(
        self, path: str, request_method: _RequestMethod
    ) -> requests.Response:

        return self._send(
            data=None, path=path, include_payload=False, request_method=request_method
        )

    def _send(
        self,
        data: str | None,
        path: str,
        include_payload: bool,
        request_method: _RequestMethod,
    ) -> requests.Response:
        url = f"{self._lambda_url}/{path}"
        match request_method:
            case "POST":
                return requests.post(
                    url,
                    data=data if include_payload else None,
                    timeout=self._timeout,
                )
            case "GET":
                return requests.get(
                    url,
                    data=data if include_payload else None,
                    timeout=self._timeout,
                )


class RemoteClient:
    """HTTP client for remote testing."""

    def __init__(
        self,
        api_url: str,
        auth_headers: dict[str, str],
        timeout: timedelta = timedelta(seconds=5),
    ):
        self._api_url = api_url
        self._default_headers = auth_headers | {"Content-Type": "application/fhir+json"}
        self._timeout = timeout.total_seconds()

    def send(
        self,
        data: str,
        path: str,
        request_method: _RequestMethod,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:

        return self._send(
            data=data,
            path=path,
            include_payload=True,
            request_method=request_method,
            headers=headers,
        )

    def send_without_payload(
        self,
        path: str,
        request_method: _RequestMethod,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:

        return self._send(
            data=None,
            path=path,
            include_payload=False,
            request_method=request_method,
            headers=headers,
        )

    def _send(
        self,
        data: str | None,
        path: str,
        include_payload: bool,
        request_method: _RequestMethod,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        url = f"{self._api_url}/{path}"
        merged_headers = self._default_headers | (headers or {})
        match request_method:
            case "POST":
                return requests.post(
                    url,
                    data=data if include_payload else None,
                    headers=merged_headers,
                    timeout=self._timeout,
                )
            case "GET":
                return requests.get(
                    url,
                    data=data if include_payload else None,
                    headers=merged_headers,
                    timeout=self._timeout,
                )


@pytest.fixture(scope="module")
def base_url() -> str:
    """Retrieves the base URL of the currently deployed application."""
    return _fetch_env_variable("BASE_URL", str)


@pytest.fixture
def hostname() -> str:
    """Retrieves the hostname of the currently deployed application."""
    return _fetch_env_variable("HOST", str)


@pytest.fixture
def client(request: pytest.FixtureRequest, base_url: str) -> Client:
    env = request.config.getoption("--env")

    if env == "local":
        return LocalClient(lambda_url=base_url)
    elif env == "remote":
        return _create_remote_client(request)
    else:
        raise ValueError(f"Unknown env: {env}")


def _create_remote_client(request: pytest.FixtureRequest) -> RemoteClient:
    """Create a RemoteClient with appropriate auth headers based on test markers."""
    proxy_url = request.getfixturevalue("nhsd_apim_proxy_url")
    default_auth_headers = request.getfixturevalue("nhsd_apim_auth_headers")

    has_status_marker = request.node.get_closest_marker("status_auth_headers")
    has_merged_marker = request.node.get_closest_marker("status_merged_auth_headers")

    if has_merged_marker:
        status_headers = request.getfixturevalue("status_endpoint_auth_headers")
        auth_headers = default_auth_headers | status_headers
    elif has_status_marker:
        auth_headers = request.getfixturevalue("status_endpoint_auth_headers")
    else:
        auth_headers = default_auth_headers

    return RemoteClient(api_url=proxy_url, auth_headers=auth_headers)


def _fetch_env_variable[T](name: str, _: type[T]) -> T:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is not set.")
    return cast("T", value)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default="local",
        help="Environment to run tests against",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    env = config.getoption("--env")

    if env == "remote":
        for item in items:
            item.add_marker(
                pytest.mark.nhsd_apim_authorization(
                    access="application", level="level3"
                )
            )
