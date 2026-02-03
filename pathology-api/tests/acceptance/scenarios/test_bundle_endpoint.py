"""
Provides the scenario bindings for the bundle endpoint feature file.
"""

from pytest_bdd import scenario

from tests.acceptance.steps.bundle_endpoint_steps import *  # noqa: F403,S2208 - Required to import all hello world steps.


@scenario("bundle_endpoint.feature", "Send a valid Bundle")
def test_send_valid_bundle() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass


@scenario("bundle_endpoint.feature", "Sending an invalid bundle")
def test_sending_invalid_bundle() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass
