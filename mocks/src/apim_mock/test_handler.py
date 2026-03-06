import string
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from apim_mock.handler import (
    _generate_random_token,
    _get_jwk_key_from_url_by_kid,
    _get_jwt_headers,
    _validate_assertions,
    _validate_payload,
    check_valid_uuid4,
    handle_request,
)


class TestHandleRequest:
    @patch("jwt.decode")
    @patch("jwt.get_unverified_header")
    @patch("apim_mock.handler._generate_random_token")
    @patch("apim_mock.handler.time")
    @patch("apim_mock.handler.write_token_to_table")
    def test_handle_request(
        self,
        write_token_mock: MagicMock,
        time_mock: MagicMock,
        generate_random_token_mock: MagicMock,
        jwt_get_unverified_header_mock: MagicMock,
        jwt_decode_mock: MagicMock,
    ) -> None:
        jwt_get_unverified_header_mock.return_value = {
            "alg": "RS512",
            "kid": "DEV-1",
        }
        jwt_decode_mock.return_value = {
            "iss": "api_key",
            "sub": "api_key",
            "exp": 1772212239,
            "jti": "7632b48d-0e2f-43e5-93a9-d339c1bcddf8",
        }
        time_mock.return_value = 1772212240
        generate_random_token_mock.return_value = "test_token"

        payload = {
            "grant_type": "client_credentials",
            "client_assertion_type": [
                "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
            ],
            "client_assertion": ["testing"],
        }

        response = handle_request(payload)

        assert response == {
            "access_token": "test_token",
            "expires_in": "599",
            "token_type": "Bearer",
        }
        write_token_mock.assert_called_with(
            {
                "access_token": "test_token",
                "expiresAt": 1772212839,
                "ddb_index": "",
                "sessionId": "test_token",
                "type": "access_token",
            }
        )

    @pytest.mark.parametrize(
        ("payload", "error_message"),
        [
            pytest.param(
                {
                    "client_assertion_type": [
                        "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                    ],
                    "client_assertion": ["testing"],
                },
                "grant_type is missing",
            ),
            pytest.param(
                {
                    "grant_type": ["client_credentials"],
                    "client_assertion": ["testing"],
                },
                (
                    "Missing or invalid client_assertion_type - "
                    "must be 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'"
                ),
            ),
            pytest.param(
                {
                    "grant_type": ["client_credentials"],
                    "client_assertion_type": [
                        "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                    ],
                },
                "Missing client_assertion",
            ),
        ],
    )
    def test_invalid_payload(self, payload: dict[str, Any], error_message: str) -> None:
        with pytest.raises(ValueError, match=error_message):
            _validate_payload(payload)

    @pytest.mark.parametrize(
        ("unverified_headers", "error_message"),
        [
            pytest.param(
                {"alg": "RS512"},
                "Missing 'kid' header in client_assertion JWT",
            ),
            pytest.param(
                {"alg": "RS256", "kid": "DEV-1"},
                (
                    "Invalid 'alg' header in client_assertion JWT - "
                    "unsupported JWT algorithm - must be 'RS512'"
                ),
            ),
        ],
    )
    @patch("jwt.get_unverified_header")
    def test_invalid_jwt_headers(
        self,
        jwt_get_unverified_header_mock: MagicMock,
        unverified_headers: dict[str, Any],
        error_message: str,
    ) -> None:
        jwt_get_unverified_header_mock.return_value = unverified_headers
        with pytest.raises(ValueError, match=error_message):
            _get_jwt_headers("test")

    def test_get_jwk_key(self) -> None:
        error_message = (
            "Invalid 'kid' header in client_assertion JWT - no matching public key"
        )
        with pytest.raises(ValueError, match=error_message):
            _get_jwk_key_from_url_by_kid("TEST-1")

    @pytest.mark.parametrize(
        ("assertions", "error_message"),
        [
            pytest.param(
                {
                    "iss": "api_key",
                    "exp": 1772212239,
                    "jti": "7632b48d-0e2f-43e5-93a9-d339c1bcddf8",
                },
                "Missing or non-matching 'iss'/'sub' claims in client_assertion JWT",
            ),
            pytest.param(
                {
                    "iss": "wrong_key",
                    "sub": "wrong_key",
                    "exp": 1772212239,
                    "jti": "7632b48d-0e2f-43e5-93a9-d339c1bcddf8",
                },
                "Invalid 'iss'/'sub' claims in client_assertion JWT",
            ),
            pytest.param(
                {
                    "iss": "api_key",
                    "sub": "api_key",
                    "exp": 1772212239,
                },
                "Missing 'jti' claim in client_assertion JWT",
            ),
            pytest.param(
                {
                    "iss": "api_key",
                    "sub": "api_key",
                    "exp": 1772212239,
                    "jti": "invalid uuid",
                },
                "Invalid UUID4 value for jti",
            ),
            pytest.param(
                {
                    "iss": "api_key",
                    "sub": "api_key",
                    "jti": "7632b48d-0e2f-43e5-93a9-d339c1bcddf8",
                },
                "Missing exp claim in assertions",
            ),
        ],
    )
    def test_validate_assertions(
        self, assertions: dict[str, Any], error_message: str
    ) -> None:
        with pytest.raises(ValueError, match=error_message):
            _validate_assertions(assertions)

    def test_generate_random_token(self) -> None:
        token = _generate_random_token()
        assert len(token) == 15
        assert all(
            c
            in "-._~+/"
            + string.ascii_uppercase
            + string.ascii_lowercase
            + string.digits
            for c in token
        )

    def test_check_valid_uuid4(self) -> None:
        assert check_valid_uuid4("ca8d399f-6a6a-4e2d-a7df-43d902c78429")
        assert not check_valid_uuid4("invalid-uuid")
