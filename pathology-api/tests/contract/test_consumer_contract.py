"""Consumer contract tests using Pact for the pathology API.

This test suite acts as a consumer that defines the expected
interactions with the provider (the Flask API).
"""

import requests
from pact import Pact, match


class TestConsumerContract:
    """Consumer contract tests to define expected API behavior."""

    def test_post_bundle(self) -> None:
        """Test the consumer's expectation of the Bundle endpoint.

        This test defines the contract: when the consumer requests
        GET/PUT/POST/PATCH/TRACE/DELETE to the
        /2015-03-31/functions/function/invocations endpoint, with a valid Bundle,
        a 200 response containing the newly created Bundle is returned.
        """
        pact = Pact(consumer="PathologyAPIConsumer", provider="PathologyAPIProvider")

        request_body = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [
                {
                    "fullUrl": "patient",
                    "resource": {
                        "resourceType": "Patient",
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "nhs_number",
                        },
                    },
                }
            ],
        }

        response_body = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [
                {
                    "fullUrl": "patient",
                    "resource": {
                        "resourceType": "Patient",
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "nhs_number",
                        },
                    },
                }
            ],
            "identifier": {
                "system": "https://tools.ietf.org/html/rfc4122",
                "value": match.uuid(),
            },
            "meta": {
                "lastUpdated": match.datetime(
                    "2026-01-16T12:00:00.000Z", format="%Y-%m-%dT%H:%M:%S.%fZ"
                ),
            },
        }

        # Define the expected interaction
        (
            pact.upon_receiving("a request for the Bundle endpoint")
            .with_body(request_body)
            .with_request(
                method="POST",
                path="/",
            )
            .will_respond_with(status=200)
            .with_body(
                response_body,
                content_type="application/fhir+json",
            )
        )

        # Start the mock server and execute the test
        with pact.serve() as server:
            # Make the actual request to the mock provider
            response = requests.post(
                f"{server.url}/",
                json=request_body,
                timeout=10,
            )

            # Verify the response matches expectations
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "application/fhir+json"

        # Write the pact file after the test
        pact.write_file("tests/contract/pacts")

    def test_get_nonexistent_route(self) -> None:
        """Test the consumer's expectation when requesting a non-existent route.

        This test defines the contract: when the consumer requests
        a route that doesn't exist, they expect a 404 response.
        """
        pact = Pact(consumer="PathologyAPIConsumer", provider="PathologyAPIProvider")

        # Define the expected interaction
        (
            pact.upon_receiving("a request for a non-existent route")
            .with_request(method="GET", path="/nonexistent")
            .will_respond_with(status=404)
        )

        # Start the mock server and execute the test
        with pact.serve() as server:
            # Make the actual request to the mock provider
            response = requests.get(f"{server.url}/nonexistent", timeout=10)

            # Verify the response matches expectations
            assert response.status_code == 404

        # Write the pact file after the test
        pact.write_file("tests/contract/pacts")
