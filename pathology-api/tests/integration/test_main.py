"""Integration tests for the pathology API using pytest."""

from pathology_api.fhir.r4.resources import Bundle, Patient

from tests.conftest import Client


class TestBundleEndpoint:
    """Test suite for the bundle endpoint."""

    def test_bundle_returns_200(self, client: Client) -> None:
        """Test that the bundle endpoint returns a 200 status code."""
        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="patient",
                    resource=Patient.create(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number"
                        )
                    ),
                )
            ],
        )

        response = client.send(
            data=bundle.model_dump_json(by_alias=True),
            path="FHIR/R4/Bundle",
            request_method="POST",
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/fhir+json"

        response_data = response.json()
        response_bundle = Bundle.model_validate(response_data, by_alias=True)

        assert response_bundle.bundle_type == bundle.bundle_type
        assert response_bundle.entries == bundle.entries

        assert response_bundle.identifier is not None
        response_identifier = response_bundle.identifier
        assert response_identifier.system == "https://tools.ietf.org/html/rfc4122"
        # A UUID value so can only check its presence.
        assert response_identifier.value is not None

        assert response_bundle.meta is not None
        response_meta = response_bundle.meta
        assert response_meta.last_updated is not None
        assert response_meta.version_id is None

    def test_no_payload_returns_error(self, client: Client) -> None:
        """Test that an error is returned when no payload is provided."""
        response = client.send_without_payload(
            request_method="POST", path="FHIR/R4/Bundle"
        )
        assert response.status_code == 400

        response_data = response.text
        assert response_data == "No payload provided."

        assert response.status_code == 400

    def test_empty_name_returns_error(self, client: Client) -> None:
        """Test that an error is returned when an empty name is provided."""
        response = client.send(data="", request_method="POST", path="FHIR/R4/Bundle")
        assert response.status_code == 400

        response_data = response.text
        assert response_data == "No payload provided."

    def test_invalid_request_method(self, client: Client) -> None:
        """Test that an error is returned when an invalid request method is used."""

        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="patient",
                    resource=Patient.create(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number"
                        )
                    ),
                )
            ],
        )

        response = client.send(
            data=bundle.model_dump_json(by_alias=True),
            request_method="GET",
            path="FHIR/R4/Bundle",
        )
        assert response.status_code == 404
        assert response.headers["Content-Type"] == "application/json"
        assert response.json() == {"message": "Not found", "statusCode": 404}


class TestStatusEndpoint:
    """Test suite for the status endpoint."""

    def test_status_returns_200(self, client: Client) -> None:
        """Test that the status endpoint returns a 200 status code."""
        response = client.send_without_payload(request_method="GET", path="_status")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/plain"

        response_data = response.text
        assert response_data == "OK"

    def test_invalid_request_method(self, client: Client) -> None:
        """Test that an error is returned when an invalid request method is used."""
        response = client.send(
            data="",
            request_method="POST",
            path="_status",
        )
        assert response.status_code == 404
        assert response.headers["Content-Type"] == "application/json"
        assert response.json() == {"message": "Not found", "statusCode": 404}
