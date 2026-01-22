"""Pytest configuration and shared fixtures for pathology API tests."""

import os
from datetime import timedelta
from typing import Literal, cast

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()


class Client:
    """A simple HTTP client for testing purposes."""

    def __init__(self, lambda_url: str, timeout: timedelta = timedelta(seconds=1)):
        self._lambda_url = lambda_url
        self._timeout = timeout.total_seconds()

    def send(
        self, data: str, path: str, request_method: Literal["GET", "POST"]
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
        return self._send(
            data=data, path=path, include_payload=True, request_method=request_method
        )

    def send_without_payload(
        self, path: str, request_method: Literal["GET", "POST"]
    ) -> requests.Response:
        """
        Send a request to the APIs without a payload.
        Args:
            path: The path to send the request to
            request_method: The HTTP method to use for the request
        Returns:
            Response object from the request
        """
        return self._send(
            data=None, path=path, include_payload=False, request_method=request_method
        )

    def _send(
        self,
        data: str | None,
        path: str,
        include_payload: bool,
        request_method: Literal["GET", "POST"],
    ) -> requests.Response:
        match request_method:
            case "POST":
                return requests.post(
                    f"{self._lambda_url}/{path}",
                    data=data if include_payload else None,
                    timeout=self._timeout,
                )
            case "GET":
                return requests.get(
                    f"{self._lambda_url}/{path}",
                    timeout=self._timeout,
                    data=data if include_payload else None,
                )


@pytest.fixture(scope="module")
def client(base_url: str) -> Client:
    """Create a test client for the application."""
    return Client(lambda_url=base_url)


@pytest.fixture(scope="module")
def base_url() -> str:
    """Retrieves the base URL of the currently deployed application."""
    return _fetch_env_variable("BASE_URL", str)


@pytest.fixture(scope="module")
def hostname() -> str:
    """Retrieves the hostname of the currently deployed application."""
    return _fetch_env_variable("HOST", str)


def _fetch_env_variable[T](name: str, t: type[T]) -> T:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is not set.")
    return cast("T", value)
